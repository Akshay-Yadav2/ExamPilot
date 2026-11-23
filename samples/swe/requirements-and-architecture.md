# Requirements, modelling and architecture

## Functional and non-functional requirements

Functional requirements say what the system must do, for example "a student can upload a PDF". Non-functional requirements constrain how well it does it: performance, availability, security, usability. Non-functional requirements should be measurable, such as "95% of searches return in under 300 ms", otherwise they cannot be tested.

## UML class and sequence diagrams

A class diagram shows classes with their attributes and operations and the relationships between them: association, aggregation (hollow diamond, the part can exist alone), composition (filled diamond, the part's lifetime is bound to the whole), and generalisation (hollow triangle for inheritance). A sequence diagram shows objects as lifelines and the messages between them in time order, top to bottom.

## Architecture styles

A layered architecture separates presentation, business logic and data access, and each layer only calls the one below it. A client-server architecture centralises data and logic on a server. Microservices split the system into small independently deployable services that own their data and talk over the network; they scale and deploy independently but add network failures, distributed data and operational cost.

## Version control and CI/CD

Version control records every change with an author and message and lets teams work on branches and merge. Continuous integration means merging to the main branch often, with every push triggering an automated build and test run. Continuous delivery keeps the main branch always deployable; continuous deployment goes further and releases every passing change automatically.

## Estimation and risk

Effort is often estimated with story points and planning poker, where the team agrees on relative size rather than hours. Velocity is the number of points completed per sprint and is used to forecast. Risk management identifies risks, estimates their probability and impact, and plans mitigation for the ones with the highest exposure (probability times impact).
