import numpy as np
import os
import re

def sst_tokenize(sentence):
    extraneous_pattern = re.compile(r"^(--lrb--|--rrb--|``|''|--|\.)$")
    words = []
    for word in sentence.split():
        if re.match(extraneous_pattern, word):
            continue
        words.append(word)
    return words

class SSTDataLoader(object):
    def __init__(dirname, fmt="stsa.fine.{}", word2vec_file="word2vec.sst-1"):
        self.dirname = dirname
        self.fmt = fmt
        self.word2vec_file = word2vec_file

    def load_embed_data(self):
        weights = []
        id_dict = {}
        unk_vocab_set = set()
        with open(os.path.join(self.dirname, self.word2vec_file)) as f:
            for i, line in enumerate(f.readlines()):
                word, vec = line.replace("\n", "").split(" ", 1)
                word = word.replace("#", "")
                vec = np.array([float(v) for v in vec.split(" ")])
                weights.append(vec)
                id_dict[word] = i
        with open(os.path.join(self.dirname, self.fmt.format("phrases.train"))) as f:
            for line in f.readlines():
                for word in sst_tokenize(line):
                    if word not in id_dict and word not in unk_vocab_set:
                        unk_vocab_set.add(word)
        return (id_dict, weights, list(unk_vocab_set))

    def load_sst_sets(self):
        set_names = ["phrases.train", "dev", "test"]
        def read_set(name):
            data_set = []
            with open(os.path.join(self.dirname, self.fmt.format(name))) as f:
                for line in f.readlines():
                    sentiment, sentence = line.replace("\n", "").split(" ", 1)
                    data_set.append((sentiment, sentence))
            return np.array(data_set)
        return [read_set(name) for name in set_names]

