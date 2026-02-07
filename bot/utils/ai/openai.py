
# from config.secrets import *
# from config.settings import showAiErrorAlerts
from modules.helpers import print_lg, critical_error_log, convert_to_json
from modules.ai.prompts import *

from pyautogui import confirm
from openai import OpenAI
from openai.types.model import Model
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from typing import Iterator, Literal

# These will be populated from globals() in runAiBot.py
use_AI = False
llm_api_key = ""
llm_api_url = ""
llm_model = ""
stream_output = False
showAiErrorAlerts = False

def ai_create_openai_client() -> OpenAI | None:
    '''
    Creates an OpenAI client.
    * Returns an OpenAI client configured for OpenAI API
    '''
    try:
        # Access the variables from the main bot's scope
        import __main__
        ua = getattr(__main__, 'use_AI', False)
        ak = getattr(__main__, 'llm_api_key', "")
        au = getattr(__main__, 'llm_api_url', "https://api.openai.com/v1/")
        am = getattr(__main__, 'llm_model', "gpt-3.5-turbo")
        
        print_lg("Creating OpenAI client...")
        if not ua:
            return None

        # Create client with OpenAI endpoint
        client = OpenAI(api_key=ak)

        print_lg("---- SUCCESSFULLY CREATED OPENAI CLIENT! ----")
        print_lg(f"Using API URL: {au}")
        print_lg(f"Using Model: {am}")
        return client
    except Exception as e:
        error_message = f"Error occurred while creating OpenAI client."
        critical_error_log(error_message, e)
        return None

def ai_completion(client: OpenAI, messages: list[dict], response_format: dict = None, temperature: float = 0, stream: bool = stream_output) -> dict | ValueError:
    '''
    Completes a chat using OpenAI API and formats the results.
    * Takes in `client` of type `OpenAI` - The OpenAI client
    * Takes in `messages` of type `list[dict]` - The conversation messages
    * Takes in `response_format` of type `dict` for JSON representation (optional)
    * Takes in `temperature` of type `float` for randomness control (default 0)
    * Takes in `stream` of type `bool` for streaming output (optional)
    * Returns the response as text or JSON
    '''
    if not client:
        raise ValueError("OpenAI client is not available!")

    # Set up parameters for the API call
    params = {
        "model": llm_model,
        "messages": messages,
        "stream": stream,
        "timeout": 30
    }

    # Add temperature
    params["temperature"] = temperature

    # Add response format if needed
    if response_format:
        params["response_format"] = response_format

    try:
        # Make the API call
        print_lg(f"Calling OpenAI API for completion...")
        print_lg(f"Using model: {llm_model}")
        print_lg(f"Message count: {len(messages)}")
        completion = client.chat.completions.create(**params)

        result = ""

        # Process the response
        if stream:
            print_lg("--STREAMING STARTED")
            for chunk in completion:
                # Check for errors
                if chunk.model_extra and chunk.model_extra.get("error"):
                    raise ValueError(f'Error occurred with OpenAI API: "{chunk.model_extra.get("error")}"')

                chunk_message = chunk.choices[0].delta.content
                if chunk_message is not None:
                    result += chunk_message
                print_lg(chunk_message, end="", flush=True)
            print_lg("\n--STREAMING COMPLETE")
        else:
            # Check for errors
            if completion.model_extra and completion.model_extra.get("error"):
                raise ValueError(f'Error occurred with OpenAI API: "{completion.model_extra.get("error")}"')

            result = completion.choices[0].message.content

        # Convert to JSON if needed
        if response_format:
            result = convert_to_json(result)

        print_lg("\nOpenAI Answer:\n")
        print_lg(result, pretty=response_format is not None)
        return result
    except Exception as e:
        error_message = f"OpenAI API error: {str(e)}"
        print_lg(f"Full error details: {e.__class__.__name__}: {str(e)}")
        if hasattr(e, 'response'):
            print_lg(f"Response data: {e.response.text if hasattr(e.response, 'text') else e.response}")

        # If it's a connection or authentication error, provide more specific guidance
        if "Connection" in str(e):
            print_lg("This might be a network issue. Please check your internet connection.")
            print_lg("If you're behind a firewall or proxy, make sure it allows connections to OpenAI API.")
        elif "401" in str(e):
            print_lg("This appears to be an authentication error. Your API key might be invalid or expired.")
        elif "404" in str(e):
            print_lg("The requested resource could not be found. The API URL or model name might be incorrect.")
        elif "429" in str(e):
            print_lg("You've exceeded the rate limit. Please wait before making more requests.")

        raise ValueError(error_message)

def ai_extract_skills(client: OpenAI, job_description: str, stream: bool = stream_output) -> dict | ValueError:
    '''
    Function to extract skills from job description using OpenAI API.
    * Takes in `client` of type `OpenAI` - The OpenAI client
    * Takes in `job_description` of type `str` - The job description text
    * Takes in `stream` of type `bool` to indicate if it's a streaming call
    * Returns a `dict` object representing JSON response
    '''
    try:
        print_lg("Extracting skills from job description using OpenAI...")

        # Using OpenAI prompt
        prompt = extract_skills_prompt.format(job_description)
        messages = [{"role": "user", "content": prompt}]

        # OpenAI API supports json_object response format
        custom_response_format = {"type": "json_object"}

        # Call OpenAI completion
        result = ai_completion(
            client=client,
            messages=messages,
            response_format=custom_response_format,
            stream=stream
        )

        # Ensure the result is a dictionary
        if isinstance(result, str):
            result = convert_to_json(result)

        return result
    except Exception as e:
        critical_error_log("Error occurred while extracting skills with OpenAI!", e)
        return {"error": str(e)}

def ai_answer_question(
    client: OpenAI,
    question: str, options: list[str] | None = None,
    question_type: Literal['text', 'textarea', 'single_select', 'multiple_select'] = 'text',
    job_description: str = None, about_company: str = None, user_information_all: str = None,
    stream: bool = stream_output
) -> dict | ValueError:
    '''
    Function to answer a question using OpenAI AI.
    * Takes in `client` of type `OpenAI` - The OpenAI client
    * Takes in `question` of type `str` - The question to answer
    * Takes in `options` of type `list[str] | None` - Options for select questions
    * Takes in `question_type` - Type of question (text, textarea, single_select, multiple_select)
    * Takes in optional context parameters - job_description, about_company, user_information_all
    * Takes in `stream` of type `bool` - Whether to stream the output
    * Returns the AI's answer
    '''
    try:
        print_lg(f"Answering question using OpenAI AI: {question}")

        # Prepare user information
        user_info = user_information_all or ""

        # Prepare prompt based on question type
        prompt = ai_answer_prompt.format(user_info, question)

        # Add options to the prompt if available
        if options and (question_type in ['single_select', 'multiple_select']):
            options_str = "OPTIONS:\n" + "\n".join([f"- {option}" for option in options])
            prompt += f"\n\n{options_str}"

            if question_type == 'single_select':
                prompt += "\n\nPlease select exactly ONE option from the list above."
            else:
                prompt += "\n\nYou may select MULTIPLE options from the list above if appropriate."

        # Add job details for context if available
        if job_description:
            prompt += f"\n\nJOB DESCRIPTION:\n{job_description}"

        if about_company:
            prompt += f"\n\nABOUT COMPANY:\n{about_company}"

        messages = [{"role": "user", "content": prompt}]

        # Call OpenAI completion
        result = ai_completion(
            client=client,
            messages=messages,
            temperature=0.1,  # Slight randomness for more natural responses
            stream=stream
        )

        return result
    except Exception as e:
        critical_error_log("Error occurred while answering question with OpenAI!", e)
        return {"error": str(e)}

def ai_close_openai_client(client: OpenAI) -> None:
    '''
    Function to close the OpenAI client.
    * Takes in `client` of type `OpenAI` - The OpenAI client to close
    * OpenAI clients don't require explicit closing, but this function is for consistency
    '''
    try:
        if client:
            print_lg("OpenAI client closed (no explicit action needed).")
        else:
            print_lg("No OpenAI client to close.")
    except Exception as e:
        critical_error_log("Error occurred while closing OpenAI client!", e)

