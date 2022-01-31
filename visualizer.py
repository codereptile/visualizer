import argparse
import visualizer

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(description='Visualize C++ / Python code')
    argument_parser.add_argument('mode', choices=['cpp', 'py'])
    argument_parser.add_argument('--target', required=True,
                                 help='Directory / file to parse')
    argument_parser.add_argument('--scale', required=False, default=1, type=float,
                                 help='Scale of all objects')

    args = argument_parser.parse_args()

    viz = visualizer.Visualizer(args.scale)

    if args.mode == 'cpp':
        viz.parse(args.target, visualizer.ParseModes.CPP)
    elif args.mode == 'py':
        viz.parse(args.target, visualizer.ParseModes.PYTHON)

    viz.run()

