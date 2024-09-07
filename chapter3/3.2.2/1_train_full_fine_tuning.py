import logging
from dataclasses import dataclass, field
import os
import random
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, TrainingArguments
from trl.commands.cli_utils import  TrlParser
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
        set_seed,

)
from trl import setup_chat_format
from peft import LoraConfig

from trl import (
   SFTTrainer)


from sklearn.model_selection import train_test_split

# Load dataset from the hub

from huggingface_hub import login

login(
    token="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",
    add_to_git_credential=True
)

dataset = load_dataset("beomi/KoAlpaca-v1.1a")
columns_to_remove = list(dataset["train"].features)

system_prompt = "당신은 다양한 분야의 전문가들이 제공한 지식과 정보를 바탕으로 만들어진 AI 어시스턴트입니다. 사용자들의 질문에 대해 정확하고 유용한 답변을 제공하는 것이 당신의 주요 목표입니다. 복잡한 주제에 대해서도 이해하기 쉽게 설명할 수 있으며, 필요한 경우 추가 정보나 관련 예시를 제공할 수 있습니다. 항상 객관적이고 중립적인 입장을 유지하면서, 최신 정보를 반영하여 답변해 주세요. 사용자의 질문이 불분명한 경우 추가 설명을 요청하고, 당신이 확실하지 않은 정보에 대해서는 솔직히 모른다고 말해주세요."
 
train_dataset = dataset.map(
    lambda sample: 
    { 'messages' : [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sample['instruction']},
        {"role": "assistant", "content": sample['output']}]
                   },
)

train_dataset = train_dataset.map(remove_columns=columns_to_remove,batched=False)
train_dataset = train_dataset["train"].train_test_split(test_size=0.1, seed=42)

train_dataset["train"].to_json("train_dataset.json", orient="records", force_ascii=False)
train_dataset["test"].to_json("test_dataset.json", orient="records", force_ascii=False)


LLAMA_3_CHAT_TEMPLATE = (
    "{% for message in messages %}"
        "{% if message['role'] == 'system' %}"
            "{{ message['content'] }}"
        "{% elif message['role'] == 'user' %}"
            "{{ '\n\nHuman: ' + message['content'] +  eos_token }}"
        "{% elif message['role'] == 'assistant' %}"
            "{{ '\n\nAssistant: '  + message['content'] +  eos_token  }}"
        "{% endif %}"
    "{% endfor %}"
    "{% if add_generation_prompt %}"
    "{{ '\n\nAssistant: ' }}"
    "{% endif %}"
)


@dataclass
class ScriptArguments:
    dataset_path: str = field(
        default=None,
        metadata={
            "help": "데이터셋 파일 경로"
        },
    )
    model_name: str = field(
    default=None, metadata={"help": "SFT 학습에 사용할 모델 ID"}
    )
    max_seq_length: int = field(
        default=512, metadata={"help": "SFT Trainer에 사용할 최대 시퀀스 길이"}
    )
    question_key: str = field(
    default=None, metadata={"help": "지시사항 데이터셋의 질문 키"}
    )
    answer_key: str = field(
    default=None, metadata={"help": "지시사항 데이터셋의 답변 키"}
    )


def training_function(script_args, training_args):    
    # 데이터셋 불러오기 
    train_dataset = load_dataset(
        "json",
        data_files=os.path.join(script_args.dataset_path, "train_dataset.json"),
        split="train",
    )
    test_dataset = load_dataset(
        "json",
        data_files=os.path.join(script_args.dataset_path, "test_dataset.json"),
        split="train",
    )

    # 토크나이저 및 데이터셋 chat_template으로 변경하기      
    tokenizer = AutoTokenizer.from_pretrained(script_args.model_name, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.chat_template = LLAMA_3_CHAT_TEMPLATE
    tokenizer.padding_side = 'right'
    # template dataset
    def template_dataset(examples):
        return{"text":  tokenizer.apply_chat_template(examples["messages"], tokenize=False)}
    
    train_dataset = train_dataset.map(template_dataset, remove_columns=["messages"])
    test_dataset = test_dataset.map(template_dataset, remove_columns=["messages"])
    
    # print random sample
    with training_args.main_process_first(
        desc="Log a few random samples from the processed training set"
    ):
        for index in random.sample(range(len(train_dataset)), 2):
            print(train_dataset[index]["text"])

    # Model 및 파라미터 설정하기 
    model = AutoModelForCausalLM.from_pretrained(
        script_args.model_name,
        attn_implementation="sdpa", # SDPA를 사용하고, 대안으로 'flash_attention_2'를 사용할 수 있음
        torch_dtype=torch.bfloat16,
        use_cache=False if training_args.gradient_checkpointing else True,  # 그래디언트 체크포인팅을 사용할 때는 True가 필요함 
    )
    
    if training_args.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    # Train 설정 
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        dataset_text_field="text",
        eval_dataset=test_dataset,
        max_seq_length=script_args.max_seq_length,
        tokenizer=tokenizer,
        packing=True,
        dataset_kwargs={
            "add_special_tokens": False,  
            "append_concat_token": False, 
        },
    )

    checkpoint = None
    if training_args.resume_from_checkpoint is not None:
        checkpoint = training_args.resume_from_checkpoint
    trainer.train(resume_from_checkpoint=checkpoint)

    if trainer.is_fsdp_enabled:
        trainer.accelerator.state.fsdp_plugin.set_state_dict_type("FULL_STATE_DICT")
    trainer.save_model()
    
if __name__ == "__main__":

    parser = TrlParser((ScriptArguments, TrainingArguments))
    script_args, training_args = parser.parse_args_and_config()    
    
    if training_args.gradient_checkpointing:
        training_args.gradient_checkpointing_kwargs = {"use_reentrant": True}
    
    # set seed
    set_seed(training_args.seed)
  
    # launch training
    training_function(script_args, training_args)