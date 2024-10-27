# Unbreakable rules
* All code must be written in Python3
* pip3 is the package manager, manage requirements.txt carefully
* Use pytest for testing
* Use black for formatting
* Use isort for sorting imports
* All new code must have 80% or greater test coverage
* All new code must have 80% or greater type checking coverage

# Veracity rail rules
* Do not overload the veracity rail concept.
* It must be
  * Simple
  * Extremely lightweight and flexible
* It must NOT
  * Do not hardcode any particular "kind" of trust rail or entity
    * While we want it to be capable of semantic closeness as a form of a rail, we do not want that to be the only kind of rail. That's silly.

# Progression rules
* Do NOT continue once you believe you've made a single test pass. Report success and allow us to test before you attempt new things. ALWAYS.