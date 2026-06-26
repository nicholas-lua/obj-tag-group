import pickle
import re
import hashlib
from collections import defaultdict

class Tag_Group:
    def __init__(self):
        self.tags = defaultdict(set)
        self.hashes = defaultdict(set)
        self.unhash = {}

    def hash_item(self, obj):
        """Uses pickle to create a key for an item"""
        try:
            pickled_data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
            item_hash = hashlib.sha256(pickled_data).hexdigest()
            return item_hash, pickled_data
        except (pickle.PicklingError, AttributeError, TypeError):
            raise TypeError(f"""Object of type {type(obj).__name__} cannot be serialized with pickle.
           Ensure it doesn't contain unpicklable elements like open files or lambdas.""")

    def tag_object(self, obj, tags):
        """
        Associates one or more tags with an arbitrary object.
        'tags' can be a single string or an iterable of strings.
        """
        key, pickled_data = self.hash_item(obj)
        self.unhash[key] = pickled_data
        
        if isinstance(tags, str):
            tags = (tags,)
        
        for tag in tags:
            self.tags[key].add(tag)
            self.hashes[tag].add(key)
    
    def untag_object(self, obj, tags = None):
        """
        Removes tags from an object.
        
        If 'tags' is provided (string or iterable of strings), only those tags will be removed.
        If no tags are provided, completely removes an object and all its associated tags from tracking.
        """
        key, _ = self.hash_item(obj)
        if key not in self.unhash:
            return
        
        if tags is not None:
            if isinstance(tags, str):
                tags = (tags,)
            
            for tag in tags:
                if tag in self.tags[key]:
                    self.tags[key].discard(tag)
                if tag in self.hashes and key in self.hashes[tag]:
                    self.hashes[tag].discard(key)
                    if not self.hashes[tag]:
                        del self.hashes[tag]
            
            if not self.tags[key]:
                del self.tags[key]
                del self.unhash[key]
        
        else:
            item_tags = self.tags.pop(key, set())
            for tag in item_tags:
                if key in self.hashes[tag]:
                    self.hashes[tag].discard(key)
                if not self.hashes[tag]:
                    del self.hashes[tag]
            del self.unhash[key]

    def get_tags(self, obj):
        """Returns the set of tags associated with a specific object."""
        obj_key, _ = self.hash_item(obj)
        return self.tags.get(obj_key, set())

    def filter_tags(self, pattern, flags=0):
        """
        Filters and returns a list of objects where at least one 
        associated tag matches the provided regular expression.
        """
        compiled_search = re.compile(pattern, flags).search
        matches = set()

        for tag, hashset in self.hashes.items():
            if compiled_search(tag):
                matches.update(hashset)

        return [pickle.loads(self.unhash[hashed_item]) for hashed_item in matches]
    
    def save_to_file(self, filename):
        """Serializes the entire Tag_Group registry state to a file."""
        with open(filename, 'wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
            
    @classmethod
    def load_from_file(cls, filename):
        """
        Loads and returns a saved Tag_Group instance from a file.
        If the file doesn't exist, returns a fresh, empty Tag_Group instance.
        """
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"File '{filename}' not found. Initializing a new registry.")
            return cls()