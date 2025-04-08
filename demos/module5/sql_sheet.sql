-- ACL to let user go out everywhere (host =>'*'), it's not required for Oracle Base Database.
begin
 -- Allow all hosts for HTTP/HTTP_PROXY
 dbms_network_acl_admin.append_host_ace(
     host =>'*',
     lower_port => 443,
     upper_port => 443,
     ace => xs$ace_type(
     privilege_list => xs$name_list('http', 'http_proxy'),
     principal_name => upper('admin'),
     principal_type => xs_acl.ptype_db)
 );
 end;
 /


-- DBMS_CLOUD credentials
-- Some examples are based on DBMS_CLOUD, that is included in Autonomous DB.
-- If you need to install it (for example on Base Database) you can refer to: https://support.oracle.com/knowledge/Oracle%20Cloud/2748362_1.html
begin
     DBMS_CLOUD.CREATE_CREDENTIAL (
         credential_name => 'xxxxxxxxxxxxx',
         user_ocid       => 'xxxxxxxxxxxxx',
         tenancy_ocid    => 'xxxxxxxxxxxxx',
         private_key     => 'xxxxxxxxxxxxx',
         fingerprint     => 'xxxxxxxxxxxxx'
     );
 end;
 /


declare
     jo json_object_t;
begin
     jo := json_object_t();
     jo.put('user_ocid','xxxxxxxxxxxxx');
     jo.put('tenancy_ocid','xxxxxxxxxxxxx');
     jo.put('compartment_ocid','xxxxxxxxxxxxx');
     jo.put('private_key','xxxxxxxxxxxxx');
     jo.put('fingerprint','xxxxxxxxxxxxx');
     dbms_vector.create_credential(
         credential_name   => 'OCI_CRED',
         params            => json(jo.to_string)
     );
 end;
 /


SELECT
     dbms_vector.utl_to_embedding(
         'hello',
         json('{
             "provider": "OCIGenAI",
             "credential_name": "OCI_CRED",
             "url": "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com/20231130/actions/embedText",
             "model": "cohere.embed-multilingual-v3.0"
         }')
     )
 FROM dual;


CREATE TABLE ai_extracted_data AS
SELECT
    j.chunk_id,
    j.chunk_offset,
    j.chunk_length,
    j.chunk_data
FROM
    -- divide a blob into chunks (utl_to_chunks):
    (select * from dbms_vector_chain.utl_to_chunks(
        dbms_vector_chain.utl_to_text(
            to_blob(
                DBMS_CLOUD.GET_OBJECT('OCI_CRED_BUCKET', 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/xxxxxxxxxxxxx/n/intoraclerohit/b/GenAI-Agents/o/faq.txt')
            )
        ), json('{"max":"200", "normalize":"all", "overlap":"20"}')
        )
    ),
    JSON_TABLE(column_value, '$'
        COLUMNS (
            chunk_id NUMBER PATH '$.chunk_id',
            chunk_offset NUMBER PATH '$.chunk_offset',
            chunk_length NUMBER PATH '$.chunk_length',
            chunk_data CLOB PATH '$.chunk_data'
        )
    ) j;


select * from ai_extracted_data;


select count(*) from ai_extracted_data;


-- Create vector table from an existing table
-- There is a quota limit for running the embedding model. For datasets with more than 400 records, we can repeatedly load the data or write a script to load data in batches.
-- In the following table ai_extracted_data, chunk_id is the record id while chunk_data is the content column.
create table ai_extracted_data_vector as (
     select chunk_id as docid, to_char(chunk_data) as body, dbms_vector.utl_to_embedding(
         chunk_data,
         json('{
             "provider": "OCIGenAI",
             "credential_name": "OCI_CRED",
             "url": "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com/20231130/actions/embedText",
             "model": "cohere.embed-multilingual-v3.0"
         }')
     ) as text_vec
     from ai_extracted_data
     where chunk_id <= 400
 );


insert into ai_extracted_data_vector
select chunk_id as docid, to_char(chunk_data) as body, dbms_vector.utl_to_embedding(
     chunk_data,
     json('{
         "provider": "OCIGenAI",
         "credential_name": "OCI_CRED",
         "url": "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com/20231130/actions/embedText",
         "model": "cohere.embed-multilingual-v3.0"
     }')
     ) as text_vec
 from ai_extracted_data
 where chunk_id > 400;


 select * from ai_extracted_data_vector;


 select count(*) from ai_extracted_data_vector;


-- Create function from vector table
-- When returning the results, rename (alias) the record ID as 'DOCID', the content column as 'BODY', and the VECTOR_DISTANCE between text_vec and query_vec as 'SCORE'. These 3 columns are required. If the vector table includes 'URL' and 'Title' columns, rename them (alias) as 'URL' and 'TITLE' respectively.
create or replace FUNCTION retrieval_func_ai (
     p_query IN VARCHAR2,
     top_k IN NUMBER
) RETURN SYS_REFCURSOR IS
     v_results SYS_REFCURSOR;
     query_vec VECTOR;
BEGIN
     query_vec := dbms_vector.utl_to_embedding(
         p_query,
         json('{
             "provider": "OCIGenAI",
             "credential_name": "OCI_CRED",
             "url": "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com/20231130/actions/embedText",
             "model": "cohere.embed-multilingual-v3.0"
         }')
     );

     OPEN v_results FOR
         SELECT DOCID, BODY, VECTOR_DISTANCE(text_vec, query_vec) as SCORE
         FROM ai_extracted_data_vector
         ORDER BY SCORE
         FETCH FIRST top_k ROWS ONLY;

     RETURN v_results;
 END;


-- Run & check the function
-- Display the DOCID and SCORE
DECLARE
     v_results SYS_REFCURSOR;
     v_docid VARCHAR2(100);
     v_body VARCHAR2(4000);
     v_score NUMBER;
     p_query VARCHAR2(100) := 'Tell me about Oracle Free Tier Account?';
     top_k PLS_INTEGER := 10;
BEGIN
     v_results := retrieval_func_ai(p_query, top_k);

     DBMS_OUTPUT.PUT_LINE('DOCID | BODY | SCORE');
     DBMS_OUTPUT.PUT_LINE('--------|------|------');

     LOOP
         FETCH v_results INTO v_docid, v_body, v_score;
         EXIT WHEN v_results%NOTFOUND;

         DBMS_OUTPUT.PUT_LINE(v_docid || ' | ' || v_body || ' | ' || v_score);
     END LOOP;

     CLOSE v_results;
 END;
