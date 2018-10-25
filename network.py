import os
import time
from scapy.all import *
from scapy.plist import PacketList
from collections import deque, Counter
from utils import queue_get_all

pkt_list = []
_first = True
start_time = 0
results = {'src': [], 'dst': [], 'sport': [], 'dport': []}


class NetSniffer(object):

    def __init__(self, q):
        self.q = q

    def _sniff(self):
        sniff(iface='docker0', store=False, prn=self.parser, filter="tcp or udp")

    def parser(self, pkt):
        global start_time
        pkt_list.append(pkt)
        results['src'].append(pkt[IP].src)
        results['dst'].append(pkt[IP].dst)
        results['sport'].append(pkt[IP].sport)
        results['dport'].append(pkt[IP].dport)

    def analysis(self):
        global results
        if _first:
            cc = self.extract_cc()
            print "[c&c]       " + cc if cc else "[c&c]      can't decect"
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cpu_percents = queue_get_all(self.q)
        avg_cpu_percent = averagenum(cpu_percents)
        if avg_cpu_percent > 7:
            num = len(results['dst'])
            if num > 8000: 
                dst = Counter(results['dst'])
                mdport = Counter(results['dport']).most_common(1)[0][0]
                if len(dst)/float(num) > 0.8:
                    print "[{time}]  Worm in progress, Scanning {port} port".format(time=current_time,
                                                                                   port=mdport)
                else:
                    mdst = dst.most_common(1)[0][0]
                    msrc = Counter(results['src']).most_common(1)[0][0]
                    msport = Counter(results['sport']).most_common(1)[0][0]

                    print "[{time}]  DDos {src}:{sport}------{dst}:{dport}".format(time=current_time,
                                                                                  src=msrc,
                                                                                  sport=msport,
                                                                                  dst=mdst,
                                                                                  dport=mdport)
            else:
                print "[{time}]  CPU {per}% Suspected mining".format(time=current_time,
                                                                    per=avg_cpu_percent)
        else:
            print "[{time}]".format(time=current_time)

        results = {'src': [],
                   'dst': [],
                   'sport': [],
                   'dport': []
                   }

    def extract_cc(self):
        global _first
        _first = False
        try:
            pkt0 = pkt_list[0]
        except IndexError:
            return None
        if TCP in pkt0:
            return "{ip}:{port}".format(ip=pkt0[IP].dst, port=pkt0.dport)



    def save(self, name):
        pcap = PacketList(pkt_list)
        if not os.path.isdir('cap'):
            os.mkdir('cap')
        wrpcap('cap/{name}.cap'.format(name=name), pcap)


def averagenum(num):
#    print num
    nsum = 0
    for i in range(len(num)):
        nsum += num[i]
    return nsum / len(num)

