KG2Narratives: Knowledge Graph based text generation
---
---
This is the repository for the findings of the paper: "From nodes to narratives: a knowledge graph based storytelling apporach"
This projects aims to generate narratives from Knowledge graphs, that are constructed from articles, and enriched by wikdata properties.

This construction is done by:
1. Creating the initial knowledge graph from a csv containing articles
2. Extending this knowledge graph with wikidata properties from the corresponding event
3. Extract sub-events, and their relations using [REBEL](https://github.com/Babelscape/rebel).
4. Merging of sub-events using Event Coreference Resolution using the [EECEP](https://github.com/Helw150/event_entity_coref_ecb_plus) model

Narratives are generated by:
1. Selecting information from the constructed narrative graph, based on the number of incoming edges of a node.
2. Generating the narrative from this selected information using [JointGT](https://github.com/thu-coai/JointGT)

The main notebook to run the project is "KG_generation.ipynb", this notebook creates the knowledge graph, and selects information from it.

---

## To finetune the REBEL model:

Link to REBEL github: https://github.com/Babelscape/rebel

The 3 files are: 
1. mapping_rebel_data.ipynb
2. rebel_finetuning_faro.ipynb
3. rebel_finetuning_faro.py

file 2, 3 *should* do the same, but the model was eventually trained using the .py file

To generate the train, validation, and test set that was used in this project execute all the cells except the last one in the "mapping_rebel_data" notebook.

To generate the correct input format for your own data, the last cell in the mapping_rebel_data.ipynb can be executed. It generates a file with the columns 'context' (the sentence) and 'triplets' with the format  \<triplet> trigger1 \<subj> trigger2 \<obj> label

To finetune the model, first change the paths in the rebel_finetuning_faro.py file to your own data, then execute the file.
The best model is determined using an average of the F1 scores of subject, object and relation, and it is saved.

inferences are made using the make_predictions function, this is automatically done in the 'KG_generation' notebook.

Event Coreference Resolution
---
---
We use the [EECEP](https://github.com/Helw150/event_entity_coref_ecb_plus) method
The code is slightly adapted to succesfully run, and code is added to convert the mentions from articles into a suitable format.
To run this part of our method please see this [repo](https://github.com/ANR-kFLOW/event_coreference_ecb_plus).

JointGT
---
---
To generate text from the selected triples we use the [JointGT](https://github.com/thu-coai/JointGT) model.
For generating the train, validation and test data by combining the WebNLG data, together with the FARO data, please execute the indicated cells in the "KG_generation" notebook.

For finetuning the JointGT model, please clone their project, and download their models which are listed on their git repo.

Then for finetuning execute the following command:
```
python3 cli_gt.py --do_train --model_name t5 --output_dir out/jointgt_t5_webnlg --train_file JointGT_data/data/webnlg/train --predict_file JointGT_data/data/webnlg/val --model_path JointGT_data/pretrain_model/jointgt_t5 --tokenizer_path JointGT_data/pretrain_model/jointgt_t5 --dataset webnlg --train_batch_size 4 --predict_batch_size 4 --max_input_length 256 --max_output_length 128 --append_another_bos --learning_rate 5e-5 --num_train_epochs 30 --warmup_steps 1600 --eval_period 800 --num_beams 5
```

For inference please use the finetuned model. Then run:
```
python cli_gt.py --do_predict --model_name t5 --output_dir JointGT_data/pretrain_model/jointgt_t5 --train_file JointGT_data/data/webnlg/train --predict_file JointGT_data/data/webnlg/test --tokenizer_path JointGT_data/pretrain_model/jointgt_t5 --dataset webnlg --predict_batch_size 24 --max_input_length 256 --max_output_length 128 --num_beams 5 --prefix test_beam5_lenpen1_
```
This will then output a file in the "output_dir" folder. Please note that this is also the folder where the finetuned model is present. For more information please see the JointGT repo.

Statistical test
---
---
Please see the notebook "statistical_test" on how the non-parametric "signed test" was performed to test whether the combined model generates better sentences, compared to the base model.