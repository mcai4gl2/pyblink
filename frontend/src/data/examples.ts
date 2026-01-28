// Example Library - Predefined schemas and messages for learning

export interface Example {
    id: string;
    title: string;
    description: string;
    schema: string;
    inputFormat: string;
    inputData: string;
}

export const EXAMPLES: Example[] = [
    {
        id: 'simple-person',
        title: 'Simple Person',
        description: 'Basic example with primitive types',
        schema: `namespace Demo

Person/1 -> string Name, u32 Age, string Email`,
        inputFormat: 'json',
        inputData: `{"$type":"Demo:Person","Name":"Alice","Age":30,"Email":"alice@example.com"}`,
    },
    {
        id: 'nested-company',
        title: 'Nested Company (Default)',
        description: 'Demonstrates nested classes and inheritance',
        schema: `namespace Demo

# Base class for address information
Address/1 -> string Street, string City, u32 ZipCode

# Employee class with nested Address
Employee/2 -> string Name, u32 Age, Address HomeAddress

# Manager subclass extends Employee with additional fields
Manager/3 : Employee -> string Department, u32 TeamSize

# Company class with nested Manager
Company/4 -> string CompanyName, Manager CEO`,
        inputFormat: 'json',
        inputData: `{"$type":"Demo:Company","CompanyName":"TechCorp","CEO":{"Name":"Alice","Age":45,"HomeAddress":{"Street":"123 Main St","City":"San Francisco","ZipCode":94102},"Department":"Engineering","TeamSize":50}}`,
    },
    {
        id: 'trading-order',
        title: 'Trading Order',
        description: 'Financial trading order with enums and decimals',
        schema: `namespace Trading

# Order side enumeration
Side/1 -> u8 Value

# Order type enumeration  
OrderType/2 -> u8 Value

# Trading order message
Order/3 -> string Symbol, decimal Price, u32 Quantity, Side OrderSide, OrderType Type`,
        inputFormat: 'json',
        inputData: `{"$type":"Trading:Order","Symbol":"AAPL","Price":150.25,"Quantity":100,"OrderSide":{"Value":1},"Type":{"Value":0}}`,
    },
    {
        id: 'dynamic-group',
        title: 'Dynamic Group',
        description: 'Shows dynamic group with polymorphic fields',
        schema: `namespace Shapes

# Base shape class
Shape/1 -> string Color

# Rectangle extends Shape
Rect/2 : Shape -> u32 Width, u32 Height

# Circle extends Shape
Circle/3 : Shape -> u32 Radius

# Frame with dynamic shape content
Frame/4 -> Shape* Content`,
        inputFormat: 'json',
        inputData: `{"$type":"Shapes:Frame","Content":{"$type":"Shapes:Rect","Color":"Red","Width":100,"Height":50}}`,
    },
    {
        id: 'sequence-example',
        title: 'Sequence Example',
        description: 'Demonstrates sequence fields (arrays)',
        schema: `namespace Data

# Student with list of grades
Student/1 -> string Name, u32[] Grades, string[] Courses`,
        inputFormat: 'json',
        inputData: `{"$type":"Data:Student","Name":"Bob","Grades":[85,92,78,95],"Courses":["Math","Science","History"]}`,
    },
    {
        id: 'optional-fields',
        title: 'Optional Fields',
        description: 'Shows optional fields with null values',
        schema: `namespace Profile

# User profile with optional fields
UserProfile/1 -> string Username, string MiddleName?, u32 Age?, string Bio?`,
        inputFormat: 'json',
        inputData: `{"$type":"Profile:UserProfile","Username":"john_doe","MiddleName":null,"Age":25,"Bio":"Software developer"}`,
    },
    {
        id: 'enum-usage',
        title: 'Enum Usage',
        description: 'Demonstrates enumerations',
        schema: `namespace Enums

# Color enumeration
Color = Red/1 | Green/2 | Blue/3

# Status enumeration (auto-numbered)
Status = Active | Inactive | Suspended

# Widget using enums
Widget/1 -> Color Color, Status Status`,
        inputFormat: 'json',
        inputData: `{"$type":"Enums:Widget","Color":"Red","Status":"Inactive"}`,
    },
];
