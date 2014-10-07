from yourgame.bootstrap import bootstrap_game
from yourgame import config


if __name__ == "__main__":
    if config.getboolean('general', 'profile'):
        import cProfile
        import pstats

        game = bootstrap_game()
        cProfile.run('game.loop()', "results.prof")

        p = pstats.Stats("results.prof")
        p.strip_dirs()
        #p.sort_stats('time').print_stats(20, "^((?!pygame).)*$")
        p.sort_stats('time').print_stats(20)
    else:
        game = bootstrap_game()
        game.loop()
