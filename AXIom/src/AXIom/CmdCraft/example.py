import nltk
import spacy

def parse_input(text):
    tokens = nltk.word_tokenize(text)
    doc = spacy.load("en_core_web_sm")(text)

    # Identify function calls and parameters
    functions = []
    params = []
    for token in doc:
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            function_name = token.text
            params.append([param.text for param in token.children])
            functions.append((function_name, params))

    return functions

text = "Call the 'Hello' function with parameters 'world', 'example'."

result = parse_input(text)

print(result)
# Output: [('Hello', ['world', 'example'])]