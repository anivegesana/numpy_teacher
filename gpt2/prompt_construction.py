from gpt2.dataset_loader import dataset_loader
from transformers import pipeline, set_seed

SAMPLE_PYTHON_PROMPT = """print("hello world!")\n"""


def main():
    dataset_train = dataset_loader(mode="py150", split="train")

    # Should the number of support rows equal the number of rows in the test_input?
    prompt, _ = incontext_code_completion(dataset_train,
                                           test_input=SAMPLE_PYTHON_PROMPT,
                                           n_support_rows=10,
                                           n_query_rows=10,
                                           n_samples=5)

    # todo: use tokenizer optimized for python code? ensure compatibility with
    #   pre-trained model to leverage old models
    # todo: fine-tune generative model on target data
    generator = pipeline('text-generation', model='gpt2')
    set_seed(42)
    generated_text = generator(prompt, num_return_sequences=5, max_length=100)

    print("generated text: ", generated_text)


# todo: replace dataset with generator class
def incontext_code_completion(dataset, test_input, n_support_rows=10, n_query_rows=10, n_samples=5):
    prompt = ''
    n_samples_generated = 0

    curr_file_idx = 0
    curr_file = dataset[curr_file_idx]
    row_in_file = 0
    while n_samples_generated < n_samples:

        # if there are not enough rows left in file, skip file
        n_rows_left = len(curr_file) - row_in_file
        if n_rows_left < n_support_rows + n_query_rows:
            curr_file_idx += 1
            curr_file = dataset[curr_file_idx]
            row_in_file = 0
            continue

        sample = ''
        # sample support rows
        for _ in range(n_support_rows):
            row_str = curr_file[row_in_file]
            sample += row_str
            row_in_file += 1

        # sample query rows
        for _ in range(n_query_rows):
            row_str = curr_file[row_in_file]
            sample += row_str
            row_in_file += 1

        sample += "\n\n"

    # add prompt for final string
    prompt += test_input

    return prompt, curr_file_idx


if __name__ == "__main__":
    main()
