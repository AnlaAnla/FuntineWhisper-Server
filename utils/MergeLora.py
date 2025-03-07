import os
import shutil
from transformers import WhisperForConditionalGeneration, WhisperFeatureExtractor, WhisperTokenizerFast, \
    WhisperProcessor
from peft import PeftModel, PeftConfig


class MergeLora:
    def __init__(self, lora_model_path, model_save_dir, temp_dir):
        # lora_model_path = "reach-vb/train/checkpoint-100"
        # model_save_dir = "Model"
        self.lora_model_path = lora_model_path
        self.model_save_dir = model_save_dir
        self.temp_dir = temp_dir

    def run(self):
        # # 获取Lora配置参数
        peft_config = PeftConfig.from_pretrained(self.lora_model_path)
        # 获取Whisper的基本模型
        base_model = WhisperForConditionalGeneration.from_pretrained(peft_config.base_model_name_or_path,
                                                                     device_map="cuda:0")
        # 与Lora模型合并
        model = PeftModel.from_pretrained(base_model, self.lora_model_path)
        feature_extractor = WhisperFeatureExtractor.from_pretrained(peft_config.base_model_name_or_path)
        tokenizer = WhisperTokenizerFast.from_pretrained(peft_config.base_model_name_or_path)
        processor = WhisperProcessor.from_pretrained(peft_config.base_model_name_or_path)

        # 合并参数
        model = model.merge_and_unload()
        model.train(False)

        # 保存的文件夹路径
        if peft_config.base_model_name_or_path.endswith("/"):
            peft_config.base_model_name_or_path = peft_config.base_model_name_or_path[:-1]

        os.makedirs(self.temp_dir, exist_ok=True)

        # 保存模型到指定目录中
        model.save_pretrained(self.temp_dir, max_shard_size='4GB')
        feature_extractor.save_pretrained(self.temp_dir)
        tokenizer.save_pretrained(self.temp_dir)
        processor.save_pretrained(self.temp_dir)
        print(f'合并模型保存在：{self.temp_dir}')

        command = f"ct2-transformers-converter --model {self.temp_dir} --output_dir {self.model_save_dir} --copy_files tokenizer.json preprocessor_config.json"

        print("执行ct2格式转化")
        retVal = os.system(command)
        print("ct2模型转化完成:{}".format(retVal))
        shutil.rmtree(self.temp_dir)
        print("移除: {}".format(self.temp_dir))

        return self.model_save_dir


# if __name__ == '__main__':
#     mergeLora = MergeLora(lora_model_path=_lora_folder_path, model_save_dir=model_save_dir, temp_dir=temp_dir)
#     ct2_save_directory = mergeLora.run()