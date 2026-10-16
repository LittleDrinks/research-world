"""Persisted entry shapes emitted by Pi 1.2.0's entry_appended event."""
from jsonschema import Draft202012Validator, ValidationError

_TEXT={'type':'string','minLength':1}
_CONTENT={'type':['string','array']}
_FIELDS={
    'custom':{'customType':_TEXT},
    'context_edit':{'targetId':_TEXT,'replacement':{'oneOf':[
        {'type':'null'},{'type':'object','required':['content'],'properties':{'content':_CONTENT}}]}},
    'message':{'message':{'type':'object','required':['role'],'properties':{'role':_TEXT}}},
    'thinking_level_change':{'thinkingLevel':_TEXT},
    'model_change':{'provider':_TEXT,'modelId':_TEXT},
    'usage':{'kind':_TEXT,'provider':_TEXT,'model':_TEXT,'usage':{'type':'object'}},
    'compaction':{'summary':{'type':'string'},'firstKeptEntryId':_TEXT,'tokensBefore':{'type':'number','minimum':0}},
    'branch_summary':{'fromId':_TEXT,'summary':{'type':'string'}},
    'custom_message':{'customType':_TEXT,'content':_CONTENT,'display':{'type':'boolean'}},
    'label':{'targetId':_TEXT},
    'session_info':{},
}
_OPTIONAL={'name':{'type':'string'},'label':{'type':'string'}}
_SCHEMA={
    'type':'object','required':['type','id','parentId','timestamp'],
    'properties':{'id':_TEXT,'parentId':{'type':['string','null']},
                  'timestamp':{'type':'string','pattern':r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'},**_OPTIONAL},
    'oneOf':[{'properties':{'type':{'const':kind},**fields},'required':list(fields)} for kind,fields in _FIELDS.items()],
}
_VALIDATOR=Draft202012Validator(_SCHEMA)


def validate_entry(entry):
    try:
        _VALIDATOR.validate(entry)
    except ValidationError:
        raise ValueError('pi session entry is invalid') from None
    return entry
