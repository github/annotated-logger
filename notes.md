Should support the ability to configure via a logging config.

The AnnotatedLogger class would take params that let it build/override parts of the config.

Need to sort out how we do the mock on the handler then. Have the mock fixture pull in a fixture for what handler to do and then if you don't do that you can override that fixture? How does it work with multiple handlers?


The overall goal is to be able to support the case where you want to configure multiple output streams (handlers) with different filters. AKA, output with a different log level that filters/formats for actions notifications at the same time as a normal logger

Also, move base_attribute support into the plugin base and also store the values we add in the annotated (annotated, action and so on). Then make a function that lets a plugin ask for the bits of a record that were added by the caller or the caller and the annotated_logger.
