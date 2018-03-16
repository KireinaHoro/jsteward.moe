Title: Conversion Sequence Precedence in C++
Date: 2018-03-17 01:00
Modified: 2018-03-17 01:00
Category: C++
Tags: c++, language
Slug: conversion-sequence-precedence-cpp

## The story

Consider the following code snippet:

```cpp
class A;

class B { 
    public: 
        B() {} 

        B(A&) { // conversion constructor that takes cv-unqualified A
            cout << "called B's conversion constructor" << endl; 
        } 
};

class A { 
    public: 
        operator B() const { // conversion operator that takes cv-qualified A
            cout << "called A's conversion operator" << endl; 
            return B(); 
        } 
};

int main()
{
    A a;
    B bb = static_cast<B>(a); // who gets called here? case 1
    B b = A();                // who gets called here? case 2
    return 0;
}
```

The output for the above code snippet is:

```plain
called B's conversion constructor
called A's conversion operator
```

The exhibited behaviour completely blew me down. Why does a __cast__ call the _conversion constructor_ and an __initialization__
call the _conversion operator_? Isn't the expected behaviour completely the reverse? After some analysis, this became clear,
though in an unexpected way.

## Case 1

This case is fairly simple.

[`[expr.static.cast/4]`](http://eel.is/c++draft/expr.static.cast#4):

> An expression e can be explicitly converted to a type T if [...] overload resolution for a direct-initialization of an object or reference of type T from e would find at least one viable function ([over.match.viable]). If T is a reference type, the effect is the same as performing the declaration and initialization
>
> > T t(e);
>
> for some invented temporary variable t ([dcl.init]) and then using the temporary variable as the result of the conversion. Otherwise, the result object is direct-initialized from e. 

Thus `static_cast<B>(a)` results in `A`'s conversion constructor getting called, regardless of presence of the conversion operator;
while if the conversion constructor `B::B(A &)` gets deleted, the following rule regarding the conversion functions apply:

[`[class.conv.fct]`](http://eel.is/c++draft/class.conv.fct):

> A member function of a class X having no parameters with a name of the form
>
> > conversion-function-id:
> >     operator conversion-type-id
> > conversion-type-id:
> >     type-specifier-seq conversion-declarator_(opt)
> > conversion-declarator:
> >     ptr-operator conversion-declarator_(opt)
>
> specifies a conversion from X to the type specified by the conversion-type-id. Such functions are called conversion functions. 

Thus `A::operator B()` gets called.

## Case 2

This gets a little bit complicated. Note that in

```cpp
    B b = A();
```

`A()` is an rvalue reference. And, for the purpose of overload resolution, there's an _implicit object parameter_ for
`A::operator B()`, whose type is `cv A&`. This parameter is special that it can be bound to an rvalue even if it's an
lvalue reference to non-const type, according to the following:

[`[over.match.funcs/5]`](http://eel.is/c++draft/over.match.funcs#5):

> During overload resolution, the implied object argument is indistinguishable from other arguments. The implicit object parameter, however, retains its identity since no user-defined conversions can be applied to achieve a type match with it. For non-static member functions declared without a ref-qualifier, an additional rule applies:
>
> > even if the implicit object parameter is not const-qualified, an rvalue can be bound to the parameter as long as in all other respects the argument can be converted to the type of the implicit object parameter. [ Note: The fact that such an argument is an rvalue does not affect the ranking of implicit conversion sequences. — end note ]

and [`[over.match.copy/1]`](http://eel.is/c++draft/over.match.copy#1):

> Under the conditions specified in [dcl.init], as part of a copy-initialization of an object of class type, a user-defined conversion can be invoked to convert an initializer expression to the type of the object being initialized. Overload resolution is used to select the user-defined conversion to be invoked. [ Note: The conversion performed for indirect binding to a reference to a possibly cv-qualified class type is determined in terms of a corresponding non-reference copy-initialization. — end note ] Assuming that “cv1 T” is the type of the object being initialized, with T a class type, the candidate functions are selected as follows:
>
> > The converting constructors of T are candidate functions.
> >
> > When the type of the initializer expression is a class type “cv S”, the non-explicit conversion functions of S and its base classes are considered. When initializing a temporary object ([class.mem]) to be bound to the first parameter of a constructor where the parameter is of type “reference to possibly cv-qualified T” and the constructor is called with a single argument in the context of direct-initialization of an object of type “cv2 T”, explicit conversion functions are also considered. Those that are not hidden within S and yield a type whose cv-unqualified version is the same type as T or is a derived class thereof are candidate functions. Conversion functions that return “reference to X” return lvalues or xvalues, depending on the type of reference, of type X and are therefore considered to yield X for this process of selecting candidate functions.

together with [`[over.ics.ref/3]`](http://eel.is/c++draft/over.ics.ref#3):

> Except for an implicit object parameter, for which see [over.match.funcs], a standard conversion sequence cannot be formed if it requires binding an lvalue reference other than a reference to a non-volatile const type to an rvalue or binding an rvalue reference to an lvalue other than a function lvalue. [ Note: This means, for example, that a candidate function cannot be a viable function if it has a non-const lvalue reference parameter (other than the implicit object parameter) and the corresponding argument would require a temporary to be created to initialize the lvalue reference (see [dcl.init.ref]). — end note ]

So if the conversion constructor takes a non-const parameter, it is not viable; while the conversion operator is always viable,
which makes overload resolution always choose the conversion operator.

If we want to use temporaries for initializing via the conversion constructor, a constructor that takes an rvalue reference will
be needed, like this:

```cpp
        B(A&&) { // conversion constructor that takes cv-unqualified A as rvalue reference
            cout << "called B's conversion constructor - rvalue reference" << endl; 
        } 
```

### Rank (precedence) between conversion sequences

Another aspect to take into consideration is the rank between the conversion sequences.

[`[over.ics.rank/3.2]`](http://eel.is/c++draft/over.ics.rank#3.2):

> Standard conversion sequence S1 is a better conversion sequence than standard conversion sequence S2 if

[`[over.ics.rank/3.2.6]`](http://eel.is/c++draft/over.ics.rank#3.2.6):

> > S1 and S2 are reference bindings, and the types to which the references refer are the same type except for top-level cv-qualifiers, and the type to which the reference initialized by S2 refers is more cv-qualified than the type to which the reference initialized by S1 refers. [ Example: ... — end example ]

So, for the rvalue reference version of conversion constructor and the conversion operator,

- `B::B(A &&)` gets chosen instead of `A::operator B() const`,
- `A::operator B()` gets chosen instead of `B::B(const A &&)`,
- `B::B(A &&)` with `A::operator B()` / `B::B(const A &&)` with `A::operator B() const` both result in ambiguity.
