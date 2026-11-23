# Design patterns

A design pattern is a named, reusable solution to a recurring design problem. Patterns are grouped as creational (how objects are made), structural (how objects are composed) and behavioural (how objects communicate and share responsibility).

## Observer

Observer defines a one-to-many dependency: when the subject changes state, all registered observers are notified and update themselves. The subject keeps a list of observers and calls update() on each in notify(). The subject depends only on the abstract Observer interface, not on concrete classes, so new observers can be added without changing the subject. Typical use: UI views listening to a model, event systems.

## Decorator

Decorator attaches extra responsibilities to an object at runtime without subclassing. The decorator implements the same interface as the component it wraps, holds a reference to it, and adds behaviour before or after delegating. Decorators can be stacked, for example a buffered stream wrapping a compressed stream wrapping a file stream. It avoids the explosion of subclasses you get from combining features through inheritance.

## Adapter

Adapter converts the interface of an existing class into the interface a client expects, so classes with incompatible interfaces can work together. The adapter wraps the adaptee and translates calls. Unlike Decorator, Adapter changes the interface; Decorator keeps the interface and adds behaviour.

## Strategy

Strategy defines a family of interchangeable algorithms behind a common interface and lets the client choose one at runtime. The context holds a reference to a strategy object and delegates the work to it. It replaces long if/else chains on an algorithm type and follows the open/closed principle: new strategies are added without editing the context.

## Factory Method and Singleton

Factory Method lets a superclass define the steps for creating an object while subclasses decide which concrete class to instantiate, so client code depends on an interface instead of a concrete constructor. Singleton ensures a class has exactly one instance with a global access point. Singleton is often criticised because it introduces hidden global state and makes unit testing harder.
