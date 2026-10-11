"""Pure field-reference selectors for source-annotated compiled token trees."""
def matching_fields(tokens,wanted):
    return sorted(set(wanted)&{t['field'] for t in tokens if t.get('field') is not None})

def array_reads(tokens,field_name):
    """Return bounded EX_ArrayElement/EX_DynArrayElement selector subtrees.

    A nearby integer is not assumed to be the requested key or physical index.
    Only actual parent/child geometry locates an index expression.
    """
    result=[]
    for i,t in enumerate(tokens):
        if t.get('field')!=field_name:continue
        ancestors=[(j,p) for j,p in enumerate(tokens[:i]) if p['depth']<t['depth'] and all(x['depth']>p['depth'] for x in tokens[j+1:i+1])]
        candidates=[(j,p) for j,p in ancestors if p['opcode'] in (0x10,0x31)]
        if not candidates:continue
        j,parent=candidates[-1];end=j+1
        while end<len(tokens) and tokens[end]['depth']>parent['depth']:end+=1
        direct=[k for k in range(j+1,end) if tokens[k]['depth']==parent['depth']+1]
        if len(direct)!=2:raise ValueError('array expression child count mismatch')
        index_end=direct[1];index_tokens=tokens[direct[0]:index_end]
        result.append(dict(field=field_name,array_token_offset=parent['offset'],field_token_offset=t['offset'],
            index_expression=index_tokens,array_expression=tokens[j:end],
            literal_physical_index=index_tokens[0]['int'] if len(index_tokens)==1 and 'int' in index_tokens[0] else None))
    return result
