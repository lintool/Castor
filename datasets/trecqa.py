import os

import torch
from torchtext.data.field import Field
from torchtext.data.iterator import BucketIterator
from torchtext.data.iterator import Iterator
from torchtext.vocab import Vectors
from torchtext.data import Pipeline

from datasets.castor_dataset import CastorPairDataset
from datasets.idf_utils import get_pairwise_word_to_doc_freq, get_pairwise_overlap_features


class TRECQA(CastorPairDataset):
    NAME = 'trecqa'
    NUM_CLASSES = 2
    ID_FIELD = Field(sequential=False, tensor_type=torch.FloatTensor, use_vocab=False, batch_first=True)
    AID_FIELD = Field(sequential=False, use_vocab=False, batch_first=True)
    TEXT_FIELD = Field(batch_first=True, tokenize=lambda x: x)  # tokenizer is identity since we already tokenized it to compute external features
    EXT_FEATS_FIELD = Field(tensor_type=torch.FloatTensor, use_vocab=False, batch_first=True, tokenize=lambda x: x,
                            postprocessing=Pipeline(lambda arr, _, train: [float(y) for y in arr]))
    LABEL_FIELD = Field(sequential=False, use_vocab=False, batch_first=True)

    VOCAB_NUM = 0

    @staticmethod
    def sort_key(ex):
        return len(ex.sentence_1)

    def __init__(self, path):
        """
        Create a TRECQA dataset instance
        """
        aid_list = []
        fields = [("aid", self.AID_FIELD)]
        with open(os.path.join(path, 'ans_id.txt'), 'r') as aid_file:
            for aid in aid_file:
                aid = aid.rstrip('.\n')
                aid_list.append(aid)

        super(TRECQA, self).__init__(path, additional_fields=fields, examples_extra=aid_list, load_ext_feats=True)

    @classmethod
    def splits(cls, path, train='train-all', validation='raw-dev', test='raw-test', **kwargs):
        return super(TRECQA, cls).splits(path, train=train, validation=validation, test=test, **kwargs)

    @classmethod
    def set_vectors(cls, field, vector_path):
        if os.path.isfile(vector_path):
            stoi, vectors, dim = torch.load(vector_path)
            field.vocab.vectors = torch.Tensor(len(field.vocab), dim)

            for i, token in enumerate(field.vocab.itos):
                wv_index = stoi.get(token, None)
                if wv_index is not None:
                    field.vocab.vectors[i] = vectors[wv_index]
                else:
                    # initialize <unk> with U(-0.25, 0.25) vectors
                    field.vocab.vectors[i] = torch.FloatTensor(dim).uniform_(-0.05, 0.05)
        else:
            print("Error: Need word embedding pt file")
            print("Error: Need word embedding pt file")
            exit(1)
        return field

    @classmethod
    def iters(cls, path, vectors_name, vectors_dir, batch_size=64, shuffle=True, device=0, pt_file = False, vectors=None, unk_init=torch.Tensor.zero_):
        """
        :param path: directory containing train, test, dev files
        :param vectors_name: name of word vectors file
        :param vectors_dir: directory containing word vectors file
        :param batch_size: batch size
        :param device: GPU device
        :param vectors: custom vectors - either predefined torchtext vectors or your own custom Vector classes
        :param unk_init: function used to generate vector for OOV words
        :return:
        """

        train, validation, test = cls.splits(path)
        if not pt_file:
            if vectors is None:
                vectors = Vectors(name=vectors_name, cache=vectors_dir, unk_init=unk_init)
            cls.TEXT_FIELD.build_vocab(train, validation, test, vectors=vectors)
        else:
            cls.TEXT_FIELD.build_vocab(train, validation, test)
            cls.TEXT_FIELD = cls.set_vectors(cls.TEXT_FIELD, os.path.join(vectors_dir, vectors_name))

        cls.LABEL_FIELD.build_vocab(train, validation, test)

        cls.VOCAB_NUM = len(cls.TEXT_FIELD.vocab)

        # BucketIterator
        return Iterator.splits((train, validation, test), batch_size=batch_size, repeat=False, shuffle=shuffle, device=device)
