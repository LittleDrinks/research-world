"""Persisted entry shapes emitted by Pi 1.2.0's entry_appended event."""
from jsonschema import Draft202012Validator, ValidationError, FormatChecker

_TEXT={'type':'string','minLength':1}
_BLOCKS=[
    {'type':'object','required':['type','text'],'properties':{'type':{'const':'text'},'text':{'type':'string'}}},
    {'type':'object','required':['type','data','mimeType'],'properties':{'type':{'const':'image'},'data':{'type':'string'},'mimeType':_TEXT}},
    {'type':'object','required':['type','thinking'],'properties':{'type':{'const':'thinking'},'thinking':{'type':'string'}}},
    {'type':'object','required':['type','id','name','arguments'],'properties':{'type':{'const':'toolCall'},'id':_TEXT,'name':_TEXT,'arguments':{'type':'object'}}},
]
_CONTENT={'oneOf':[{'type':'string'},{'type':'array','items':{'oneOf':_BLOCKS}}]}
_MESSAGE={'type':'object','required':['role','content'],
          'properties':{'role':{'enum':['user','assistant','toolResult']},'content':_CONTENT}}
_FIELDS={
    'custom':{'customType':_TEXT},
    'context_edit':{'targetId':_TEXT,'replacement':{'oneOf':[
        {'type':'null'},{'type':'object','required':['content'],'properties':{'content':_CONTENT}}]}},
    'message':{'message':_MESSAGE},
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
                  'timestamp':{'type':'string','format':'date-time'},**_OPTIONAL},
    'oneOf':[{'properties':{'type':{'const':kind},**fields},'required':list(fields)} for kind,fields in _FIELDS.items()],
}
_VALIDATOR=Draft202012Validator(_SCHEMA,format_checker=FormatChecker())


def validate_entry(entry):
    try:
        _VALIDATOR.validate(entry)
    except ValidationError:
        raise ValueError('pi session entry is invalid') from None
    return entry
