if __name__ == '__main__':
    with open('pref_generated.ini', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    names = []
    for line in lines:
        if not line.startswith('custom_proxy_group='):
            continue
        pos = line.find('`')
        if pos == -1:
            continue
        group_name = line[19:pos]
        names.append(group_name)
    out = ''.join(map(lambda x: f'`[]{x}', names))
    out = '`[]DIRECT`[]🚀 节点选择' + out
    print(out)