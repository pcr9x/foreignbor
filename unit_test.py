import unittest
from unittest.mock import patch, MagicMock
from chatbot import (
    classify_intent,
    extract_entities,
    ask_for_missing_entities_yes_no,
    query_from_prolog,
)
from BERT_train import IntentClassifier
import numpy as np


class TestChatbot(unittest.TestCase):
    @patch("chatbot.intent_pipeline")
    def test_classify_intent(self, mock_intent_pipeline):
        # Mock the intent pipeline response
        mock_intent_pipeline.return_value = [{"label": "LABEL_0", "score": 0.95}]
        
        # Mock label encoder classes
        with patch("chatbot.label_encoder") as mock_label_encoder:
            mock_label_encoder.classes_ = ["injury_case", "murder_case"]
            
            # Test classify_intent
            user_input = "Someone was injured in an accident."
            intent = classify_intent(user_input)
            self.assertEqual(intent, "injury_case")

    @patch("chatbot.chat")
    def test_extract_entities(self, mock_chat):
        # Mock the chat response
        mock_response = MagicMock()
        mock_response.message.content = '{"PersonAge": "30", "Injured": "yes", "Intent": "intentional"}'
        mock_chat.return_value = mock_response
        
        # Test extract_entities
        user_input = "A 30-year-old person intentionally injured someone."
        required_keys = ["PersonAge", "Injured", "Intent"]
        extracted_entities = extract_entities(user_input, required_keys)
        
        expected_entities = {
            "PersonAge": "30",
            "Injured": "yes",
            "Intent": "intentional"
        }
        self.assertEqual(extracted_entities, expected_entities)

    @patch("builtins.input", side_effect=["yes", "ascendant"])
    def test_ask_for_missing_entities_yes_no(self, mock_input):
        # Test ask_for_missing_entities_yes_no
        extracted_entities = {
            "PersonAge": "30",
            "Injured": None,
            "VictimType": None
        }
        required_keys = ["PersonAge", "Injured", "VictimType"]
        updated_entities = ask_for_missing_entities_yes_no(extracted_entities, required_keys)
        
        expected_entities = {
            "PersonAge": "30",
            "Injured": "true",
            "VictimType": "ascendant"
        }
        self.assertEqual(updated_entities, expected_entities)

    @patch("chatbot.prolog.query")
    def test_query_from_prolog(self, mock_prolog_query):
        # Mock the Prolog query response
        mock_prolog_query.return_value = [{"S": "10 years imprisonment"}]
        
        # Test query_from_prolog
        prolog_query = "clear_case, handle_case(injury_case(person, victim, true, true, true, true, true, true, false, official)), sentence(person, S)."
        result = query_from_prolog(prolog_query)
        
        expected_result = [{"S": "10 years imprisonment"}]
        self.assertEqual(result, expected_result)

    @patch("chatbot.prolog.query")
    def test_query_from_prolog_no_results(self, mock_prolog_query):
        # Mock the Prolog query response with no results
        mock_prolog_query.return_value = []
        
        # Test query_from_prolog
        prolog_query = "clear_case, handle_case(injury_case(person, victim, false, false, false, false, false, false, false, other)), sentence(person, S)."
        result = query_from_prolog(prolog_query)
        
        self.assertEqual(result, [])


class TestBERTTrain(unittest.TestCase):
    @patch("BERT_train.Dataset.from_dict")
    @patch("BERT_train.train_test_split")
    def test_load_dataset(self, mock_train_test_split, mock_from_dict):
        # Mock dataset loading
        mock_train_test_split.return_value = (
            ["text1", "text2"], ["text3"],
            ["intent1", "intent2"], ["intent3"]
        )
        mock_from_dict.return_value = MagicMock()

        classifier = IntentClassifier()
        dataset = [
            {"text": "text1", "intent": "intent1"},
            {"text": "text2", "intent": "intent2"},
            {"text": "text3", "intent": "intent3"}
        ]
        classifier.load_dataset = MagicMock(return_value=dataset)

        # Test dataset loading
        loaded_dataset = classifier.load_dataset()
        self.assertEqual(len(loaded_dataset), 3)
        self.assertEqual(loaded_dataset[0]["text"], "text1")
        self.assertEqual(loaded_dataset[0]["intent"], "intent1")

    @patch("BERT_train.pipeline")
    def test_predict_intent(self, mock_pipeline):
        # Mock the pipeline response
        mock_pipeline.return_value = [{"label": "LABEL_0", "score": 0.95}]

        classifier = IntentClassifier()
        classifier.label_encoder.classes_ = ["intent1", "intent2"]

        # Test intent prediction
        predicted_intent, confidence = classifier.predict_intent("Sample text", mock_pipeline)
        self.assertEqual(predicted_intent, "intent1")
        self.assertAlmostEqual(confidence, 0.95)


if __name__ == "__main__":
    unittest.main()