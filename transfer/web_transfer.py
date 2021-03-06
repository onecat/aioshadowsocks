import logging

from transfer.users import User
from transfer.utils import EhcoApi


class WebTransfer:
    def __init__(self, token, url, node_id, local_address):
        self.api = EhcoApi(token, url)
        self.local_address = local_address
        self.node_id = node_id
        self.transfer_mul = 1.0

    def get_all_user_configs(self):
        '''
        拉取符合要求的用户信息
        '''

        node_id = self.node_id

        # 获取节点流量比例信息
        nodeinfo = self.api.getApi('/nodes/{}'.format(node_id))
        if not nodeinfo:
            logging.warning('没有查询到满足要求的节点，请检查自己的node_id!'
                            '当前节点ID: {}'.format(node_id))
            return
        logging.info('节点id: {} 流量比例: {}'.format(node_id, nodeinfo[0]))
        # 记录流量比例
        self.transfer_mul = float(nodeinfo[0])

        # 获取符合条件的用户信息
        data = self.api.getApi('/users/nodes/{}'.format(node_id))
        if not data:
            logging.warning('没有查询到满足要求的user，请检查自己的node_id!')
            return
        users = []
        for user_info in data:
            users.append(User(**user_info))
        configs = {'local_address': self.local_address, 'users': users}
        return configs

    def update_all_user(self, user_list):
        # 用户流量上报
        data = []
        alive_user_count = 0
        for user in user_list:
            if user.once_used_traffic > 0:
                alive_user_count += 1
                data.append({
                    'user_id': user.user_id,
                    'u': user.once_used_u * self.transfer_mul,
                    'd': user.once_used_d * self.transfer_mul
                })
            # reset user used traffic
            user.once_used_u = 0
            user.once_used_d = 0

        if len(data) > 0:
            tarffic_data = {'node_id': self.node_id,
                            'data': data}
            self.api.postApi('/traffic/upload', tarffic_data)
        # 节点人数上报
        online_data = {'node_id': self.node_id,
                       'online_user': alive_user_count}
        self.api.postApi('/nodes/online', online_data)
