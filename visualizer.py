import argparse
import visualizer

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(description='Visualize C++ / Python code')
    argument_parser.add_argument('mode', choices=['cpp', 'py'])
    argument_parser.add_argument('--target', required=True,
                                 help='Directory / file to parse')
    argument_parser.add_argument('--scale', required=False, default=1, type=float,
                                 help='Scale of all objects')
    argument_parser.add_argument('--bruteforce', required=False, default=False, type=bool,
                                 help='If true, enters \'brute-force\' mode '
                                      'and tries to ignore as many errors as possible')
    argument_parser.add_argument('--v', required=False, default=False, type=bool,
                                 help='Verbose mode - prints more information')

    args = argument_parser.parse_args()

    viz = visualizer.Visualizer(args.scale)

    if args.mode == 'cpp':
        viz.parse(args.target, visualizer.ParseModes.CPP, args.bruteforce, args.v)
    elif args.mode == 'py':
        viz.parse(args.target, visualizer.ParseModes.PYTHON, args.bruteforce, args.v)

    viz.run()
