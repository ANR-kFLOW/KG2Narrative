## This is *just* a small explanation about the relation extraction using the rebel model

Link to REBEL github: https://github.com/Babelscape/rebel

The 3 files are: 
1. mapping_rebel_data.ipynb
2. rebel_finetuning_faro.ipynb
3. rebel_finetuning_faro.py

file 2, 3 *should* do the same, but the model was eventually trained using the .py file

The last cell in the mapping_rebel_data.ipynb can be executed to generate the needed input format to the model:
A file with the columns 'context' (the sentence) and 'triplets' with the format  \<triplet> trigger1 \<subj> trigger2 \<obj> label

To finetune the model, first change the paths in the rebel_finetuning_faro.py file to your own data, then execute the file.
The best model is determined using an average of the F1 scores of subject, object and relation, and it is saved.


