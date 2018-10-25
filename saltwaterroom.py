import subprocess
from monitor import Monitor
from argparse import ArgumentParser, RawDescriptionHelpFormatter


def main():
    parse = ArgumentParser(
        description='a sample sandbox basd on docker.\nexample usage: python saltwaterroom.py ks -c "sh /tmp/ks"',
        formatter_class=RawDescriptionHelpFormatter)

    parse.add_argument("path", help="the path of the malware")
    parse.add_argument("-c", "--command",
        help="the command to start the malware. default is /tmp/filename")

    args = parse.parse_args()
    filetype = subprocess.check_output(["file", args.path])
    md5 = subprocess.check_output(["md5sum", args.path]).split(' ')[0]
    sha256 = subprocess.check_output(["sha256sum", args.path]).split(' ')[0]
    print "[file]      {path}".format(path=args.path)
    print "[filetype]  {type}".format(type=filetype.strip())
    print "[md5]       {md5}".format(md5=md5)
    print "[sha256]    {sha}".format(sha=sha256)
    Mon = Monitor(args.path, filetype)
    Mon.run(args.command)


if __name__ == '__main__':
    main()
