# Design principles

## Coupling and cohesion

Coupling is how much one module depends on others; cohesion is how closely the responsibilities inside one module belong together. Good design aims for low coupling and high cohesion: modules that do one thing well and know little about each other are easier to change, test and reuse.

## SOLID

Single responsibility: a class should have one reason to change. Open/closed: modules should be open for extension but closed for modification. Liskov substitution: objects of a subclass must be usable wherever the base class is expected without breaking correctness. Interface segregation: clients should not be forced to depend on methods they do not use. Dependency inversion: high-level modules should depend on abstractions, not on concrete low-level modules.

## Liskov substitution example

The classic violation is Square extending Rectangle. Code that sets width to 5 and height to 4 expects an area of 20, but a Square that keeps its sides equal returns 16. Square is a rectangle mathematically but not behaviourally, so inheritance is the wrong relationship here.

## Agile process and Scrum

Agile development delivers working software in short iterations and welcomes changing requirements. Scrum organises work into sprints of one to four weeks. Roles are the product owner, who orders the product backlog, the scrum master, who removes impediments, and the development team. Events are sprint planning, the daily scrum, the sprint review and the sprint retrospective. Waterfall, by contrast, runs requirements, design, implementation, testing and maintenance as sequential phases.

## User stories

A user story has the form "As a <role>, I want <goal> so that <benefit>". Good stories follow INVEST: independent, negotiable, valuable, estimable, small and testable. Acceptance criteria turn a story into checkable conditions, often written as Given/When/Then.
