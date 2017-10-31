import os

import torch
from torchtext.data.dataset import Dataset
from torchtext.data.example import Example
from torchtext.data.field import Field
from torchtext.data.iterator import BucketIterator
from torchtext.vocab import Vectors


class SICK(Dataset):

    TEXT_FIELD = Field(batch_first=True)
    LABEL_FIELD = Field(sequential=False, tensor_type=torch.FloatTensor, use_vocab=False, batch_first=True)

    @staticmethod
    def sort_key(ex):
        return len(ex.a)

    def __init__(self, path):
        """
        Create a SICK dataset instance
        """
        fields = [('a', self.TEXT_FIELD), ('b', self.TEXT_FIELD), ('label', self.LABEL_FIELD)]

        examples = []
        f1 = open(os.path.join(path, 'a.txt'), 'r')
        f2 = open(os.path.join(path, 'b.txt'), 'r')
        label_file = open(os.path.join(path, 'sim.txt'), 'r')

        for l1 in f1:
            l2 = f2.readline()
            label = label_file.readline()
            example = Example.fromlist(map(lambda s: s.rstrip('.\n'), [l1, l2, label]), fields)
            examples.append(example)

        super(SICK, self).__init__(examples, fields)

    @classmethod
    def splits(cls, path, train='train', validation='dev', test='test', **kwargs):
        return super(SICK, cls).splits(path, train=train, validation=validation, test=test, **kwargs)

    @classmethod
    def iters(cls, path, vectors_name, vectors_cache, batch_size=64, shuffle=True, device=0, vectors=None):
        """
        :param path: directory containing train, test, dev files
        :param vectors_name: name of word vectors file
        :param vectors_cache: path to word vectors file
        :param batch_size: batch size
        :param device: GPU device
        :param vectors: custom vectors - either predefined torchtext vectors or your own custom Vector classes
        :return:
        """
        if vectors is None:
            vectors = Vectors(name=vectors_name, cache=vectors_cache, unk_init=torch.Tensor.zero_)

        train, val, test = cls.splits(path)

        cls.TEXT_FIELD.build_vocab(train, vectors=vectors)

        return BucketIterator.splits((train, val, test), batch_size=batch_size, shuffle=shuffle, device=device)
