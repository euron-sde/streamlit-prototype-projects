import os
import random  # type: ignore
import string  # type: ignore
import logging
import tiktoken
import requests

from enum import Enum  # type: ignore
from openai import AsyncOpenAI
from exa_py import Exa
from urllib.parse import urlparse  # type: ignore
from pdfplumber import open as open_pdf
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

ALPHA_NUM = string.ascii_letters + string.digits
GPT4 = "gpt-4o"
GPT3 = "gpt-3.5-turbo-0125"


def get_filename_from_url(url):
    a = urlparse(url)
    return os.path.basename(a.path)


class GenerationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))


# async def extract_text_from_pdf(pdf_file: UploadFile) -> str:
async def extract_text_from_pdf(pdf_url: str) -> str:
    try:
        # Get the filename from the URL
        filename = get_filename_from_url(pdf_url)

        # Download the PDF
        download_pdf(pdf_url, filename)

        text = ""
        with open_pdf(filename) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        # Delete the PDF file
        delete_file(filename)

        return text
    except Exception as e:
        logger.error(f"Error occured in the extract text form pdf : {e}")


def filter_strings(list_of_words: list) -> str:
    try:
        final_words = [item for item in list_of_words if isinstance(
            item, str) and any(c.isalpha() for c in item)]
        final_words = final_words[:7000]
        return ' '.join(final_words)

    except Exception as e:
        logger.error(f"Error in filtering strings: {e}")
        return ""


def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)
        print(f"{filename} has been deleted.")
    else:
        print(f"{filename} does not exist.")


def download_pdf(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)


async def generate_content(messages: list, model: str = GPT4) -> dict:
    # Fetch OpenAI API key from environment variables
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key is not provided")

    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=api_key)
    if model == GPT4 and 'json' in messages[0]['content'].lower():
        res = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1,
            response_format={'type': 'json_object'}
        )
        return eval(res.choices[0].message.content)

    res = await client.chat.completions.create(
        model=GPT3,
        messages=messages,
        temperature=1,
    )

    return res.choices[0].message.content


def get_generated_image(prompt, number_of_images):
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key is not provided")

    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=api_key)
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


async def exa_search(query):
    try:
        searched_content = []
        exa = Exa(api_key=os.environ.get('EXA_API_KEY'))
        exa_response = exa.search_and_contents(query, num_results=2)
        for text in exa_response.results:
            searched_content.append(await restrict_tokens(text.text, 2000))
        return "\n".join(searched_content)
    except Exception as e:
        logger.error(f"Error in exa search: {e}")
        return None


async def internet_search(outline):
    try:
        # Internet search
        all_search_data = []
        for data in outline:
            topics_data = await exa_search(data)
            all_search_data.append(topics_data)
        return "\n".join(all_search_data)
    except Exception as e:
        logger.error(f"Error in internet search: {e}")


async def restrict_tokens(text: str, max_tokens: int = 2000):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        encoded_text = enc.encode(text)

        if len(encoded_text) > max_tokens:
            encoded_text = encoded_text[:max_tokens]
            text = enc.decode(encoded_text)

        return text
    except Exception as e:
        logger.error(f"Error in restrict tokens: {e}")
        return text


async def summarize_text(text, outline):
    try:
        SUMMERIZE_SYSTEM_PROMPT = "Please clean the following internet data: {all_search_data} and provide me the very detailed points of the data based on my outline: {outline}. Minimum length of the data should be 1000 words"

        summary_of_searched_data_messages = [
            {"role": "system", "content": SUMMERIZE_SYSTEM_PROMPT.format(
                all_search_data=text, outline=outline)}
        ]

        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        res = await client.chat.completions.create(
            model=GPT3,
            messages=summary_of_searched_data_messages,
            temperature=1,
        )

        return res.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in summarizing text: {e}")
        return text
