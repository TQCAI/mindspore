# Copyright 2019 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
from mindspore import context
import mindspore.nn as nn
from mindspore.ops import operations as P
from mindspore import Tensor
from tests.ut.python.ops.test_math_ops import VirtualLoss
import mindspore as ms
from mindspore.common.api import _executor
from mindspore.ops import composite as C
from mindspore.common.parameter import Parameter


class NetWithLoss(nn.Cell):
    def __init__(self, network):
        super(NetWithLoss, self).__init__()
        self.loss = VirtualLoss()
        self.network = network

    def construct(self, x):
        predict = self.network(x)
        return self.loss(predict)

class GradWrap(nn.Cell):
    def __init__(self, network):
        super(GradWrap, self).__init__()
        self.network = network

    def construct(self, x):
        return C.grad_all(self.network)(x)

# core dump, step_auto_parallel should SetInputs for transpose axis
def test_reshape_matmul():
    class Net(nn.Cell):
        def __init__(self):
            super().__init__()
            self.reshape = P.Reshape()
            self.matmul = P.MatMul()
            self.matmul_weight = Parameter(Tensor(np.ones([28, 64]), dtype=ms.float32), name="weight")

        def construct(self, x):
            out = self.reshape(x, (64, 28))
            out = self.matmul(out, self.matmul_weight)
            return out

    size = 8
    context.set_auto_parallel_context(device_num=size, global_rank=0)
    x = Tensor(np.ones([8*size, 28, 1, 1]), dtype=ms.float32)

    net = GradWrap(NetWithLoss(Net()))
    context.set_auto_parallel_context(parallel_mode="auto_parallel")
    net.set_auto_parallel()
    _executor.compile(net, x)


if __name__ == '__main__':
    test_reshape_matmul()