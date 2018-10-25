import time
import docker
import subprocess
from network import NetSniffer
from Queue import Queue
from utils import thread_start, timer
from error import FileFormatError, FileExecuteError


def calculate_cpu_percent(d, previous_cpu, previous_system):
    cpu_percent = 0.0
    cpu_total = float(d["cpu_stats"]["cpu_usage"]["total_usage"])
    cpu_delta = cpu_total - previous_cpu
    cpu_system = float(d["cpu_stats"]["system_cpu_usage"])
    system_delta = cpu_system - previous_system
    online_cpus = d["cpu_stats"].get("online_cpus", len(d["cpu_stats"]["cpu_usage"]["percpu_usage"]))
    if system_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
    return cpu_percent, cpu_system, cpu_total


def calculate_blkio_bytes(d):
    #return: (read_bytes, wrote_bytes), ints
    bytes_stats = graceful_chain_get(d, "blkio_stats", "io_service_bytes_recursive")
    if not bytes_stats:
        return 0, 0
    r = 0
    w = 0
    for s in bytes_stats:
        if s["op"] == "Read":
            r += s["value"]
        elif s["op"] == "Write":
            w += s["value"]
    return r, w


def calculate_network_bytes(d):
    # :return: (received_bytes, transceived_bytes), ints
    networks = graceful_chain_get(d, "networks")
    if not networks:
        return 0, 0
    r = 0
    t = 0
    for if_name, data in networks.items():
        #logger.debug("getting stats for interface %r", if_name)
        r += data["rx_bytes"]
        t += data["tx_bytes"]
    return r, t


def graceful_chain_get(d, *args):
    t = d
    for a in args:
        try:
            t = t[a]
        except (KeyError, ValueError, TypeError) as ex:
            #logger.debug("can't get %r from %s", a, t)
            return None
    return t


def stats(container, out_q):
    cpu_total = 0.0
    cpu_system = 0.0
    cpu_percent = 0.0
    for x in container.stats(decode=True, stream=True):
        blk_read, blk_write = calculate_blkio_bytes(x)
        net_r, net_w = calculate_network_bytes(x)
        mem_current = x["memory_stats"]["usage"]
        mem_total = x["memory_stats"]["limit"]
#        time = x["read"]

        cpu_percent, cpu_system, cpu_total = calculate_cpu_percent(x, cpu_total, cpu_system)

#        r = {
#            "cpu_percent": cpu_percent,
#            "mem_current": mem_current,
#            "mem_total": x["memory_stats"]["limit"],
#            "mem_percent": (mem_current / mem_total) * 100.0,
#            "blk_read": blk_read,
#            "blk_write": blk_write,
#            "net_rx": net_r,
#            "net_tx": net_w,
#            "time": time,
#            "container_id": container.id
#        }
#        yield r
        out_q.put(cpu_percent)
#        print cpu_percent


def limitnet(id, rate=10, burst=20):
    # get veth pair
    r = subprocess.check_output("docker exec -it {name} bash -c 'cat /sys/class/net/eth0/iflink'".format(name=id), shell=True).strip()
    veth = subprocess.check_output("grep -l {r} /sys/class/net/veth*/ifindex".format(r=r), shell=True).split('/')[4]
    # tc limit rate on ckservice container
    cmd = ("tc qdisc add dev {veth} ingress; "
           "tc filter add dev {veth} parent ffff: "
           "protocol ip prio 10 u32 match ip src 0.0.0.0/0 "
           "police rate {rate}kbps burst {burst}m drop").format(veth=veth,
                                                                rate=rate,
                                                                burst=burst)
    subprocess.call(cmd, shell=True)
    return veth


class Monitor(object):

    def __init__(self, path, filetype):
        self.path = path
        self.client = docker.from_env()
        self.volumes = None
        self.privileged = False
        self.image = self.image(filetype)

    def image(self, filetype):
        if "ARM" in filetype:
            self.privileged = True
            self.volumes = {'/usr/bin/qemu-arm-static':
                               {'bind': '/usr/bin/qemu-arm-static',
                                'mode': 'rw'}
                              }
            return "ioft/armhf-ubuntu:latest"
        elif "MIPS" in filetype:
            self.privileged = True
            self.volumes = {'/usr/bin/qemu-mips-static':
                                {'bind':'/usr/bin/qemu-mips-static',
                                 'mode': 'rw'}
                              }
            return "npmccallum/debian-mips:jessie"
        else:
            return "ubuntu:latest"

    def run(self, command):
        try:
            container = self.client.containers.run(
                self.image,
                stdin_open=True,
                detach=True,
                privileged=self.privileged,
                volumes=self.volumes,
                cpu_period=1000000,
                cpu_quota=100000,
                mem_limit="128m",
                command="bash"
                )
            filename = self.path.split('/')[-1]
            path_filename = "/tmp/" + filename
            subprocess.call(["docker", "cp", self.path, container.id+":"+path_filename])
            container.exec_run("chmod 777 "+path_filename, detach=True)
            veth = limitnet(container.id)
            execute_command = command if command else path_filename

            q = Queue()
            sniffer = NetSniffer(q)
            thread_start(stats, container, q)
            thread_start(sniffer._sniff)

            output = container.exec_run(execute_command)
            if output.exit_code != 0:
                if output.exit_code == 126:
                    raise FileFormatError(path_filename)
                else:
                    raise FileExecuteError(path_filename)
            print "[start operation]"
            print "-" * 76
            time.sleep(59)
            timer(sniffer.analysis)

            time.sleep(1800)
            NetSniffer.save(filename)
            subprocess.call("tc qdisc del dev {veth} ingress".format(veth=veth), shell=True)
        except Exception as ex:
            print ex
        finally:
            container.remove(force=True)
