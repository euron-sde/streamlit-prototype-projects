import os
import logging
import tiktoken

from exa_py import Exa
from openai import OpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

GPT4 = "gpt-4o"
GPT3 = "gpt-3.5-turbo-0125"

SUMMERIZATION_SYSTEM_PROMPT = """{text}

----------
Using the above text, answer the following question:

> {question}

----------
If the question cannot be answered using the text, simply summarize the text.
Include all factual information, numbers, stats etc if available.
Collect pain points of customers in this domain.
Key drivers and restraints influencing this market.
Current size and projected growth of the [specific market/industry].
Leading players in the market and what sets them apart.
Any emerging challengers or disruptor showing potential.
Key differentiators among the top contenders in the market.
You need to create summaries considering all the mentioned conditions. Moreover, length of the summaries shouldn't be less then 1000 token.
"""


def restrict_tokens(text: str) -> str:
    enc = tiktoken.get_encoding("cl100k_base")
    encoded_text = enc.encode(text)

    if len(encoded_text) > 10000:
        encoded_text = encoded_text[:8000]
        text = enc.decode(encoded_text)

    return text


def create_summery(text: str, question: str):
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=GPT3,
            messages=[
                {"role": "system", "content": SUMMERIZATION_SYSTEM_PROMPT.format(
                    text=restrict_tokens(text), question=question)}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return {"status": "error", "message": str(e), "code": "ERR_GENERATION_INTERRUPTED"}


@tool
def exa_search(query: str):
    """
    Perform a search using the Exa API and return the results as a single string.
    This function uses the Exa API to search for the given query and retrieves
    the contents of the top 2 results. The results are then concatenated into
    a single string with each result separated by a newline.
    :param query: The search query string.
    :return: A string containing the concatenated text of the top 2 search results.
    """
    exa = Exa(api_key=os.environ.get("EXA_API_KEY"))
    exa_response = exa.search_and_contents(query, num_results=5)
    summery = [create_summery(text.text, query)
               for text in exa_response.results]
    return "\n".join(summery)


@tool
def get_generated_image(prompt: str, number_of_images: int):
    """
    Generate images based on a given prompt using the OpenAI API.
    This function interacts with the OpenAI API to generate images based on the provided prompt.
    It supports generating multiple images if the number_of_images parameter is greater than 1.
    The function uses different models and image sizes based on the number of images requested.
    :param prompt: The text prompt to generate images from.
    :param number_of_images: The number of images to generate. If greater than 1, multiple images will be generated.
    :return: A string containing the URLs of the generated images. If multiple images are generated, the URLs are concatenated with a space separator.
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    if number_of_images > 1:
        image_response = client.images.generate(
            model="dall-e-2",
            prompt=f"Create an image of {prompt}",
            size="512x512",
            n=number_of_images,
            response_format="url",
        )
        return " ".join([i.url for i in image_response.data])
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=f"Create an image of {prompt}",
        size="1024x1024",
        n=1,
        response_format="url",
    )
    return image_response.data[0].url
