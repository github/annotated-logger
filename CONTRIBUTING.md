## Contributing

[fork]: https://github.com/github/annotated-logger/fork
[pr]: https://github.com/github/annotated-logger/compare
[style]: https://docs.astral.sh/ruff/

Hi there! We're thrilled that you'd like to contribute to this project. Your help is essential for keeping it great.

Contributions to this project are [released](https://help.github.com/articles/github-terms-of-service/#6-contributions-under-repository-license) to the public under the [project's open source license](LICENSE.txt).

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Developing a fix/feature

Annotated Logger uses `ruff`, `pytest`, `pyright` and `mutmut` for testing and linting. It uses [`hatch`](https://github.com/pypa/hatch) as a project manager to build and install dependencies. When developing locally it's suggested that you ensure that your editor supports `ruff` and `pyright` for inline linting. The `pytest` test suite is very quick and should be run frequently. (`mutmut`)[https://github.com/boxed/mutmut] is a mutation testing tool and is fairly slow as it runs the other three tools hundreds of times after making minor tweaks to the code. It will typically be run only once development is complete to ensure everything is fully tested.

`script/mutmut_runner` is what `mutmut` uses to see if the mutation fails, however, it's also quite useful on it's own as it runs `ruff`, `pytest` and `pyright` exiting as soon as anything fails, so it makes a good sanity check.

In addition to the tests and linting above all PRs will compare the version number in \_\_init\_\_.py with the version in `main` to ensure that new PRs results in new versions.

## Submitting a pull request

1. [Fork][fork] and clone the repository
1. Configure and install the dependencies: `script/bootstrap`
1. Make sure the tests pass on your machine: `hatch run dev:test`
1. Make sure linting passes: `hatch run dev:lint` and `hatch run dev:typing`
1. Create a new branch: `git checkout -b my-branch-name`
1. Make your change, add tests, and make sure the tests still pass
1. Push to your fork and [submit a pull request][pr]
1. Pat yourself on the back and wait for your pull request to be reviewed and merged.

Here are a few things you can do that will increase the likelihood of your pull request being accepted:

- Follow the [style guide][style].
- Write tests.
- Keep your change as focused as possible. If there are multiple changes you would like to make that are not dependent upon each other, consider submitting them as separate pull requests.
- Write a [good commit message](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).

## Resources

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
