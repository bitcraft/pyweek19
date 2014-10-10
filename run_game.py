from zort.bootstrap import bootstrap_game
from zort import config


if __name__ == "__main__":
    if config.getboolean('general', 'profile'):
        import inspect
        import cProfile
        import pstats
        from time import sleep
        from profilehooks import profile

        # calibrate the profiler
        pr = cProfile.Profile()
        #for i in range(5):
        #    print pr.calibrate(10000)

        game = bootstrap_game()
        cProfile.run('game.loop()', "results.prof")
        p = pstats.Stats("results.prof")
        p.strip_dirs()
        p.sort_stats('cumulative').print_stats(50)

    else:
        game = bootstrap_game()
        game.loop()
