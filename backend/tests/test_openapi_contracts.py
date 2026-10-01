from app.main import app


def resolve(schema,value):
    while '$ref' in value:
        value=schema['components']['schemas'][value['$ref'].split('/')[-1]]
    return value


def test_all_operations_have_explicit_success_contracts():
    schema=app.openapi()
    operations=0
    for path,item in schema['paths'].items():
        for method,operation in item.items():
            if method not in ('get','post','put','patch','delete'):
                continue
            operations+=1
            for status,response in operation['responses'].items():
                if not status.startswith('2'):
                    continue
                content=response.get('content',{})
                assert content,(path,method)
                for media,details in content.items():
                    shape=resolve(schema,details['schema'])
                    assert shape,(path,method,media)
                    if media=='application/json':
                        assert shape.get('properties'),(path,method)
    assert operations>=124


def test_important_response_fields_and_error_envelopes():
    schema=app.openapi()
    cases=[('/api/v1/inventory/days-of-stock','get','200',{'days_of_stock','safety_stock','suggested_quantity'}),
           ('/api/v1/sync/pull','get','200',{'items','next_cursor','watermark'}),
           ('/api/v1/suppliers/{identifier}/metrics','get','200',{'quantity_fulfilment_rate','eligible_order_count'}),
           ('/api/v1/reports/{kind}','get','200',{'rows','has_more'}),
           ('/api/v1/auth/refresh','post','200',{'access_token','refresh_token'})]
    for path,method,status,fields in cases:
        response=schema['paths'][path][method]['responses'][status]
        envelope=resolve(schema,response['content']['application/json']['schema'])
        data=resolve(schema,envelope['properties']['data'])
        assert fields<=set(data['properties'])
        error=schema['paths'][path][method]['responses']['422']
        assert 'error' in resolve(schema,error['content']['application/json']['schema'])['properties']
    login=resolve(schema,schema['paths']['/api/v1/auth/login']['post']['responses']['200']['content']['application/json']['schema'])
    assert 'access_token' in login['properties'] and 'data' not in login['properties']
    download=schema['paths']['/api/v1/report-jobs/{identifier}/download']['get']['responses']['200']['content']
    assert 'application/json' not in download and 'application/pdf' in download
    user=schema['components']['schemas']['UserView']['properties']
    assert not {'password_hash','token_hash','token_version'} & set(user)
