# Software testing

Testing executes the software to find defects. It can show the presence of bugs but never prove their absence. Verification asks "are we building the product right?" and validation asks "are we building the right product?".

## Levels of testing

Unit tests check a single function or class in isolation and run in milliseconds. Integration tests check that components work together, for example the service and the real database. System tests check the whole application against the requirements, and acceptance tests check it against what the customer actually needs. The test pyramid recommends many unit tests, fewer integration tests and only a few slow end-to-end tests.

## Black-box and white-box testing

Black-box testing designs test cases from the specification without looking at the code: equivalence partitioning splits inputs into classes expected to behave the same, and boundary value analysis tests the edges of each class, such as 0, 1 and the maximum. White-box testing designs cases from the code structure, aiming to cover statements, branches or paths.

## Coverage

Statement coverage measures the share of statements executed by the tests. Branch coverage requires every branch of every decision to be taken both ways, and is stronger than statement coverage. 100% coverage does not mean the code is correct: tests can execute a line without checking its result, and missing requirements produce no code to cover.

## Test doubles

A test double replaces a real dependency in a test. A stub returns canned answers. A mock also records how it was called so the test can verify the interaction. A fake is a working lightweight implementation, such as an in-memory database. Doubles make unit tests fast and deterministic, but too many mocks couple tests to implementation details.

## Test-driven development

TDD repeats a short cycle: red (write a failing test for the next small piece of behaviour), green (write the simplest code that passes), refactor (clean up while the tests stay green). Benefits are a regression suite built as you go and designs that are easy to test. Regression testing means re-running existing tests after a change to make sure nothing that worked before is broken.
