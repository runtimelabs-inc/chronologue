"""
test_generalize_trace.py

Unit test for generalize_trace.py
- Uses modelresponses
- Validates output structure
- Ensures schema compliance
"""

import unittest
from unittest.mock import patch
from modules.generalize_trace import process_trace
from modules.schema import validate_memory_trace

mock_trace = {
    "timestamp": "2025-04-24T10:30:00Z",
    "content": "Talked with Dr. Smith at UCSF about the fMRI results from Subject A12. Need to follow up with consent form on Monday."
}

mock_personal_response = "Remember to follow up on the consent form by Monday."
mock_generalized_response = "Discussed imaging results with a medical professional.\n[neuroimaging, follow-up, documentation]"

class TestGeneralizeTrace(unittest.TestCase):

    @patch("modules.generalize_trace.generate_personal_response")
    @patch("modules.generalize_trace.generate_generalized_trace")
    def test_process_trace(self, mock_generalize, mock_personal):
        mock_personal.return_value = mock_personal_response
        mock_generalize.return_value = {
            "timestamp": "2025-04-24T10:30:00Z",
            "summary": "Discussed imaging results with a medical professional.",
            "tags": ["neuroimaging", "follow-up", "documentation"],
            "source": "generalized"
        }

        response, generalized = process_trace(mock_trace)

        self.assertIsInstance(response, str)
        self.assertIn("follow up", response)

        self.assertIsInstance(generalized, dict)
        self.assertIn("summary", generalized)
        self.assertIn("tags", generalized)
        self.assertTrue(isinstance(generalized["tags"], list))

        # Optional: Validate against schema if extended
        validate_memory_trace({"timestamp": mock_trace["timestamp"], "content": mock_trace["content"]})


if __name__ == '__main__':
    unittest.main()
