import argparse
import visualizer

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(description='Visualize C++ / Python code')
    argument_parser.add_argument('mode', choices=['cpp', 'py'])
    argument_parser.add_argument('--target', required=True,
                                 help='Directory / file to parse')

    args = argument_parser.parse_args()

    file_parser = visualizer.Parser()

    if args.mode == 'cpp':
        file_parser.parse(args.target, visualizer.ParseModes.CPP)
    elif args.mode == 'py':
        file_parser.parse(args.target, visualizer.ParseModes.PYTHON)

