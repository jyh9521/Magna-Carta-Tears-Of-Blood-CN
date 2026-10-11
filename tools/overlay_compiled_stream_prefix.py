"""Source-bound, all-alignment-consensus overlay of observed cached prefixes.

The repetition grammar is a source oracle, not an independent stream decoder.
Every permitted original alignment must produce the same modified prefix.
Ambiguous transformations, multiple headers/ends, or unknown bytes fail closed.
Function metadata after the observed prefix is retained byte-for-byte.
"""
from font_poc import require,digest
from audit_stream_script_correspondence import repetition_sites,header_positions,align_prefix


def consensus_prefix(bundle,offset,raw,modified,script,edits):
    sites=repetition_sites(raw,script);start,end=script['start'],script['end']
    original_alignment=align_prefix(bundle,offset,raw,script)
    require(original_alignment['matched'] and original_alignment['unique_end'],'cached prefix has no unique original end')
    expected_end=original_alignment['ends'][0]['offset'];atoms={};byte_changes={}
    for q in edits:
        old_at,new_at=q['old_offset'],q['new_offset'];old_len,new_len=q['old_bytes'],q['new_bytes']
        require(0<=old_at<old_at+old_len<=len(raw) and 0<=new_at<new_at+new_len<=len(modified),'cached edit bounds')
        if old_at<start:require(old_at+old_len<=start,'cached edit crosses script header');continue
        require(old_at+old_len<=end,'cached edit crosses prefix end')
        if q['label'].startswith('literal-'):
            require(not any(i in sites for i in range(old_at,old_at+old_len)),'literal intersects repetition site')
            require(old_at not in atoms,'duplicate cached literal edit');atoms[old_at]=(old_len,modified[new_at:new_at+new_len])
        else:
            require(old_len==new_len,'unsupported variable-width cached operand')
            for i in range(old_len):
                require(old_at+i not in byte_changes,'overlapping cached operand edits')
                byte_changes[old_at+i]=modified[new_at+i]
    # Header length does not change for these literal/operand transformations.
    require(bundle[offset:offset+start]==raw[:start],'cached prefix header mismatch')
    states={(offset+start,modified[:start])};at=start;peak=1
    while at<end:
        next_states=set()
        if at in atoms:
            count,new=atoms[at];needle=raw[at:at+count]
            for pos,output in states:
                if bundle[pos:pos+count]==needle:next_states.add((pos+count,output+new))
            at+=count
        else:
            old=raw[at];new=byte_changes.get(at,old)
            for pos,output in states:
                if pos<len(bundle) and bundle[pos]==old:
                    next_states.add((pos+1,output+bytes([new])))
                    if at in sites and pos+1<len(bundle) and bundle[pos+1]==old:next_states.add((pos+2,output+bytes([new,new])))
            at+=1
        require(next_states,'cached prefix correspondence failed during transformation')
        require(len(next_states)<=256,'cached transformation state limit exceeded')
        states=next_states;peak=max(peak,len(states))
    require({pos for pos,_ in states}=={expected_end},'cached transformation end disagreement')
    outputs={output for _,output in states};require(len(outputs)==1,'cached transformation differs between valid original alignments')
    new=outputs.pop();old=bundle[offset:expected_end]
    return dict(label='compiled-prefix',offset=offset,original=old,modified=new),dict(original_offset=offset,original_end=expected_end,original_bytes=len(old),modified_bytes=len(new),original_sha256=digest(old),modified_sha256=digest(new),original_alignment_paths=original_alignment['ends'][0]['alignment_paths'],all_alignment_outputs_identical=True,peak_states=peak,independent_stream_reader=False,metadata_tail_modified=False,runtime_verified=False)


def unique_prefix(bundle,raw,modified,script,edits):
    positions=header_positions(bundle,raw[:script['start']]);require(len(positions)==1,'cached Function header missing or ambiguous')
    return consensus_prefix(bundle,positions[0],raw,modified,script,edits)
