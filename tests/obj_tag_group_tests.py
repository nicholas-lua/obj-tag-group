import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import unittest
import os
import tempfile
from obj_tag_group import Tag_Group

class TestTagGroup(unittest.TestCase):
    def setUp(self):
        """Initialize a fresh Tag_Group before each test."""
        self.registry = Tag_Group()

    def test_tagging_and_retrieval_unhashable_types(self):
        """Test tagging and retrieving normally unhashable types like lists and dicts."""
        my_list = [1, 2, 3]
        my_dict = {"a": 1, "b": 2}
        
        self.registry.tag_object(my_list, "list-tag")
        self.registry.tag_object(my_dict, ["dict-tag", "shared-tag"])
        
        # Verify specific object tags
        self.assertEqual(self.registry.get_tags(my_list), {"list-tag"})
        self.assertEqual(self.registry.get_tags(my_dict), {"dict-tag", "shared-tag"})

    def test_tag_with_single_str_and_iterable(self):
        """Verify both single strings and iterables work for assigning tags."""
        obj = "test_string"
        
        # Tag with a string
        self.registry.tag_object(obj, "single")
        self.assertIn("single", self.registry.get_tags(obj))
        
        # Tag with an iterable
        self.registry.tag_object(obj, ["multi1", "multi2"])
        self.assertEqual(self.registry.get_tags(obj), {"single", "multi1", "multi2"})

    def test_untag_specific_tags(self):
        """Test removing only selected tags from an object."""
        obj = [1, 2]
        self.registry.tag_object(obj, ["tag1", "tag2", "tag3"])
        
        # Remove a single tag
        self.registry.untag_object(obj, "tag1")
        self.assertEqual(self.registry.get_tags(obj), {"tag2", "tag3"})
        
        # Remove multiple tags via list
        self.registry.untag_object(obj, ["tag2"])
        self.assertEqual(self.registry.get_tags(obj), {"tag3"})

    def test_untag_entire_object(self):
        """Test completely untagging an object removes it from the internal indexes."""
        obj = {"key": "val"}
        self.registry.tag_object(obj, ["tag1", "tag2"])
        
        # Calling untag without arguments should wipe it out completely
        self.registry.untag_object(obj)
        
        self.assertEqual(self.registry.get_tags(obj), set())
        # Assert clean up of internal reverse index
        self.assertNotIn("tag1", self.registry.hashes)
        self.assertNotIn(obj, self.registry.filter_tags("tag1"))

    def test_filter_tags_regex(self):
        """Verify regular expression search works effectively across all tags."""
        self.registry.tag_object([1], "apple-juice")
        self.registry.tag_object([2], "banana-shake")
        self.registry.tag_object([3], "orange-juice")
        
        # Match ends with 'juice'
        juice_results = self.registry.filter_tags(r"juice$")
        self.assertEqual(len(juice_results), 2)
        self.assertIn([1], juice_results)
        self.assertIn([3], juice_results)
        
        # Match partial string
        ana_results = self.registry.filter_tags(r"ana")
        self.assertEqual(ana_results, [[2]])

    def test_unpicklable_object_raises_exception(self):
        """Ensure attempting to register an unpicklable object safely raises a TypeError."""
        # Lambdas cannot be pickled natively
        unpicklable_obj = lambda x: x + 1
        
        with self.assertRaises(TypeError):
            self.registry.tag_object(unpicklable_obj, "lambda-tag")

    def test_save_and_load_from_file(self):
        """Verify state preservation when writing to and loading from disk."""
        obj1 = {"user": "Alice"}
        obj2 = ["admin", "staff"]
        
        self.registry.tag_object(obj1, "auth-user")
        self.registry.tag_object(obj2, "roles")
        
        # Use a temporary file context to avoid side effects
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_filename = tmp.name
        
        try:
            # Save state
            self.registry.save_to_file(tmp_filename)
            
            # Load into a fresh Registry pointer
            loaded_registry = Tag_Group.load_from_file(tmp_filename)
            
            # Assert data consistency
            self.assertEqual(loaded_registry.get_tags(obj1), {"auth-user"})
            self.assertEqual(loaded_registry.filter_tags("roles"), [obj2])
            
        finally:
            # Cleanup filesystem
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

    def test_load_non_existent_file(self):
        """Ensure loading a missing file gracefully falls back to an empty Tag_Group instance."""
        fallback_registry = Tag_Group.load_from_file("this_file_definitely_does_not_exist.pkl")
        self.assertIsInstance(fallback_registry, Tag_Group)
        self.assertEqual(len(fallback_registry.unhash), 0)

if __name__ == '__main__':
    unittest.main()