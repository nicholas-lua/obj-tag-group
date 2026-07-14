# obj_tag_group

A searchable registry that allows you to attach text tags to almost any Python object.

Objects are indexed by their serialized content, allowing for quick filtering of items using regular expression searches on their associated tags.


## Important Notes

1. The save/load-to-file feature of this package uses Python's `pickle` module. **Never load a saved registry file from an untrusted source**, as this can result in arbitrary code execution during deserialization.

2. This package will fail to work on objects that cannot be serialized, such as lambda functions.

3. Tagging works by creating a full copy of the object in memory, and will not reflect any future changes made to the object(s).


## Motivation

In Python, categorizing objects is usually done by modifying an object's class to include a `tags` attribute, or mapping the objects in a dictionary. However, this becomes a problem for unhashable objects such as the native set or dict.

Originally, the package was intended to simply allow users to tag and filter Unicode characters for easy searching, but was later extended to work on other data types as well, necessitating support for unhashable types.


## Features

- Add / remove tags from most Python objects, even unhashable ones such as dictionaries and lists, as well as custom classes.
- Filter and retrieve objects using regular expression queries.
- Save the entire tagged registry to disk and load it back later.


## Installation

```bash
pip install obj_tag_group
```

## Quickstart

```python
from obj_tag_group import Tag_Group

# 1. Initialize the Registry
reg = Tag_Group()

# 2. Create and Tag Objects
test_1 = {1: "Apple", 2: ("Lemon", "Mango")}
test_2 = ["Mango", "Pineapple", "Cabbage"]
test_3 = "Lettuce"
test_4 = ("beef", "ham")

reg.tag_object(test_1, tags=["dict", "fruit"])
reg.tag_object(test_2, tags=["list", "fruit", "vegetable"])
reg.tag_object(test_3, tags=["string", "vegetable"])
reg.tag_object(test_4, tags=["tuple", "meat"])

# 3. Filter Objects by Tags (Example: find objects with "fruit", "vegetable", or both)
results = reg.filter_tags(pattern=r"vegetable|fruit")
print(results)
# Output (not necessarily in the same order): [{1: 'Apple', 2: ('Lemon', 'Mango')}, ['Mango', 'Pineapple', 'Cabbage'], 'Lettuce']

```


## User Guide

### 1. Tagging Objects and Handling Errors
The `tag_object` method accepts arbitrary Python structures. If an object is of a type that cannot be serialized by `pickle` (e.g., live file streams, database connections, or lambda functions), the system will catch the error and raise a `TypeError`.

```python
# Tagging an unhashable dictionary structure
reg.tag_object({"user_id": 101}, tags=["auth", "active"])

# Triggering a serialization safety catch
try:
    reg.tag_object(lambda x: x + 1, tags=["function"])
except TypeError as e:
    print(e)  # Output: Object of type function cannot be serialized with pickle. [...]

```

### 2. Modifying and Removing Tags

The behavior of the `untag_object` method varies based on the arguments provided:

1. Remove specific tags: Pass a string or an iterable of strings to strip those explicit tags while leaving the object in the registry. Objects that have no remaining tags will be removed automatically.

2. Completely untrack an object: Omit the `tags` parameter entirely to wipe the object and all of its associated tags completely from memory.

```python
# Remove only the "active" tag
reg.untag_object({"user_id": 101}, tags="active")

# Completely stop tracking this object across the entire registry
reg.untag_object({"user_id": 101})
```


### 3. Filtering with Regex Flags

The `filter_tags` method forwards any standard Python regular expression options to the `re` compiler. For example, case-insensitive queries can be implemented using `re.IGNORECASE`.

```python
import re

# Matches "VEGETABLE", "Vegetable", or "vegetable"
results = reg.filter_tags(pattern=r"^VEGETABLE$", flags=re.IGNORECASE)
```

Note on Result Ordering: The list returned by `filter_tags()` is inherently unordered due to the underlying hash table indexing. If your application relies on a specific sequence, sort the output list manually after retrieval.


### 4. Saving and Loading to Files
The entire `Tag_Group` registry (including all tracked objects, hashes, and tags) can be saved to a file on disk and reloaded to return to exactly where you left off. 

* `save_to_file(filename)`: Serializes the current registry state using high-performance pickling.
* `load_from_file(filename)`: A class method that restores your data. If the specified file does not exist, it catches the error and returns a completely fresh, empty `Tag_Group` instance instead of crashing.

```python
# Save your current session state to disk
reg.save_to_file("my_registry.pkl")

# Load your session back into a new variable later (or in a different script)
from obj_tag_group import Tag_Group
loaded_reg = Tag_Group.load_from_file("my_registry.pkl")
```

Security Reminder: As detailed in the `Important Notes` section, `load_from_file` uses `pickle` to load serialized data. Only load files created by yourself or trusted parties to prevent arbitrary code execution.


## Developer Guide

This guide outlines the internal architecture of `obj_tag_group` and provides setup instructions for modifying the package.


### 1. Internal Architecture & State Management
The library relies on three internal data structures within the `Tag_Group` class to map objects, hashes, and tags:

* `self.unhash = {}`: A standard dictionary mapping a SHA-256 string hash to the raw `pickle` byte stream of the tracked object. This acts as our primary object storage database.
* `self.tags = defaultdict(set)`: A dictionary mapping an object's SHA-256 hash to a Python `set` of string tags assigned to it.
* `self.hashes = defaultdict(set)`: A dictionary mapping a specific string tag back to a `set` of object SHA-256 hashes, enabling faster regular expression pattern filtering.


### 2. Local Environment Setup
To set up a local development environment, clone the repository and install it in editable/development mode:

```bash
# Clone the repository
git clone https://github.com/nicholas-lua/obj_tag_group.git
cd obj_tag_group

# Install the package in editable mode with development tools
pip install -e .
```


### 3. Running Tests

We use `pytest` to maintain codebase reliability. Before finalizing changes, ensure all tests pass cleanly by running the test suite:

```bash
# Install testing dependencies
pip install pytest

# Execute tests
pytest
```