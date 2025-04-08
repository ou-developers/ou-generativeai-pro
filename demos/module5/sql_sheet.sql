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
         credential_name => 'OCI_CRED_BUCKET',
         user_ocid       => 'ocid1.user.oc1..aaaaaaaa3vspheideczn3n5tkqdcrajftuvfnohzwke6dhfweb57lmynj7va',
         tenancy_ocid    => 'ocid1.tenancy.oc1..aaaaaaaaxy6bh46cdnlfpaibasc6dotowv32hc2sbj4ph3ocxtfxhhva2hna',
         private_key     => 'MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDXbAGkrlr+LpJc009ntZyeSUm5HV591Uo/2eoqE4dR//bfqI8iNypgRAXxWY5YsyULIGMkkrYoS1AUVeVMrkvr1GwMRqLUZY826XHUB0HxQuphFEfSHJWe8ELOna+SWRdXNqYxUm7wl61YbhZfioluzhdRXZnS9d/NAVaW2pnnnenU45Pa0lF5KP+fbpYw3CJpiGF4ntv0CsFZUqIFQOfJoSVYks4xsURGV4+erm4WezzBPzaezl08MswJlqQOH7PGfzbn068ZfG5O1fvZvcpQM/lVByAMdr+Z1OROh2oIXzQVRQksyq2UpeEkzFhhpJ39UlBiU2lkI2tx8hcwIDjlAgMBAAECgf9FAFOGbFK5GDHJieXlUkbYbKEwqjeaFrexvBtFXvv5SAPLoDI4w3LPYvqEVCtEPh2fcsBO9q9iOL1txhWseifXYjM5u2Zsohs9e4j6YVi97rEkZ1qZ8o36WvsLM3cJaYAQb3DMW5stdWgQ6zI/aCCdXWYaqeCbsiX9hHA34c1qYpQIQQbzcTjmQjptnd2480lf3TCOCN1b/UIWfNdG7sVX6g8ybzYlVYNsIXo/GL5KEsvVoLfEP55bLl2g/A6NpsoGYRQUZ8zNtjnob4hxtbUQfGLU8p6lz8O86pYQUq+8BcMETyDvlROkTXx7EJc69W6IkjyWqUDhif4OGMCyAsECgYEA8FAIR8s/g7ivTsh8WBnU9AV/rHMCrpiPPJo9ESn6kcy+emnomBTlZPUeTkjHalEsFzsEc7vQ0Ucyphi5ukx2xSSUN6/5qi7WqMcHdP/gCt1LBGMAH1jNRachwNsUkdDXdKWDZLnePw8r6j80a0wXfqV99ljtylBl41IkY+rUyV0CgYEA5XwDsnICpzi62mcKTKQWwzr6dUZ4hqn8tnTzcl8aepbYC12DePvfqwEp9TsiXRosibbbYN/5OOYEI2mGes8O4yei3pDgo3vIBSgU9H6SWSEi3hmSFLJQxkf9DajOKTVRIBge2MHf55Pm1TtJp3rcOeduC306aE+0j6Kltwq3TSkCgYEAhKAWwdCpIAAoODmrbk/rWDVErh7XJxapTo/tDfD2CctOgG684Fn/9ATXkerWq5Va2QNIRLst1qINkN9qeSfEEK9MYaNsDYFGFOWq9uZUdoqE4UnmAmbW+w7vMOl347W3gvfpmQh/YJv155S0UFcxTEL3TqLrsVFHufpWfRJYFz0CgYA83zB73RInGT03Qa3RtpTzJGnbQd4mmmCWZV9OLzvu2KRmH2AIb4dc7OocSptK5u55eS+n+sE4/oqKeitZ2CKyzoi9UODFfMgJ1h/42ronOkrtbwr4wnP6pI3TWbuV4raqNLu583NZEjpgxWE8M7LHCUR/d7BOixXyI8qhSw5kQQKBgQCM701VZuUe1BuZJenHcg0JfwUJA4GNctZHT0h2us0dWDp5j+1dzWJWICiEGaihutyMxZd14x/PXWYXW68MPFgZt/XP49HqSW918IEZNiBaOiFohIuDJiAyql3NqOu/cEvDf5y7xp+hPqZsBrbwyEDf8U9PQBTe8nVABAURPmSGpg==',
         fingerprint     => '36:a3:17:e5:79:da:32:35:b5:c9:d4:b5:08:cc:88:1f'
     );
 end;
 /


declare
     jo json_object_t;
begin
     jo := json_object_t();
     jo.put('user_ocid','ocid1.user.oc1..aaaaaaaa3vspheideczn3n5tkqdcrajftuvfnohzwke6dhfweb57lmynj7va');
     jo.put('tenancy_ocid','ocid1.tenancy.oc1..aaaaaaaaxy6bh46cdnlfpaibasc6dotowv32hc2sbj4ph3ocxtfxhhva2hna');
     jo.put('compartment_ocid','ocid1.compartment.oc1..aaaaaaaa7ppatdkvw4tgc5gj4gdkacgobf63bd4iysmhshfksqhgr5v55d5q');
     jo.put('private_key','MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDXbAGkrlr+LpJc009ntZyeSUm5HV591Uo/2eoqE4dR//bfqI8iNypgRAXxWY5YsyULIGMkkrYoS1AUVeVMrkvr1GwMRqLUZY826XHUB0HxQuphFEfSHJWe8ELOna+SWRdXNqYxUm7wl61YbhZfioluzhdRXZnS9d/NAVaW2pnnnenU45Pa0lF5KP+fbpYw3CJpiGF4ntv0CsFZUqIFQOfJoSVYks4xsURGV4+erm4WezzBPzaezl08MswJlqQOH7PGfzbn068ZfG5O1fvZvcpQM/lVByAMdr+Z1OROh2oIXzQVRQksyq2UpeEkzFhhpJ39UlBiU2lkI2tx8hcwIDjlAgMBAAECgf9FAFOGbFK5GDHJieXlUkbYbKEwqjeaFrexvBtFXvv5SAPLoDI4w3LPYvqEVCtEPh2fcsBO9q9iOL1txhWseifXYjM5u2Zsohs9e4j6YVi97rEkZ1qZ8o36WvsLM3cJaYAQb3DMW5stdWgQ6zI/aCCdXWYaqeCbsiX9hHA34c1qYpQIQQbzcTjmQjptnd2480lf3TCOCN1b/UIWfNdG7sVX6g8ybzYlVYNsIXo/GL5KEsvVoLfEP55bLl2g/A6NpsoGYRQUZ8zNtjnob4hxtbUQfGLU8p6lz8O86pYQUq+8BcMETyDvlROkTXx7EJc69W6IkjyWqUDhif4OGMCyAsECgYEA8FAIR8s/g7ivTsh8WBnU9AV/rHMCrpiPPJo9ESn6kcy+emnomBTlZPUeTkjHalEsFzsEc7vQ0Ucyphi5ukx2xSSUN6/5qi7WqMcHdP/gCt1LBGMAH1jNRachwNsUkdDXdKWDZLnePw8r6j80a0wXfqV99ljtylBl41IkY+rUyV0CgYEA5XwDsnICpzi62mcKTKQWwzr6dUZ4hqn8tnTzcl8aepbYC12DePvfqwEp9TsiXRosibbbYN/5OOYEI2mGes8O4yei3pDgo3vIBSgU9H6SWSEi3hmSFLJQxkf9DajOKTVRIBge2MHf55Pm1TtJp3rcOeduC306aE+0j6Kltwq3TSkCgYEAhKAWwdCpIAAoODmrbk/rWDVErh7XJxapTo/tDfD2CctOgG684Fn/9ATXkerWq5Va2QNIRLst1qINkN9qeSfEEK9MYaNsDYFGFOWq9uZUdoqE4UnmAmbW+w7vMOl347W3gvfpmQh/YJv155S0UFcxTEL3TqLrsVFHufpWfRJYFz0CgYA83zB73RInGT03Qa3RtpTzJGnbQd4mmmCWZV9OLzvu2KRmH2AIb4dc7OocSptK5u55eS+n+sE4/oqKeitZ2CKyzoi9UODFfMgJ1h/42ronOkrtbwr4wnP6pI3TWbuV4raqNLu583NZEjpgxWE8M7LHCUR/d7BOixXyI8qhSw5kQQKBgQCM701VZuUe1BuZJenHcg0JfwUJA4GNctZHT0h2us0dWDp5j+1dzWJWICiEGaihutyMxZd14x/PXWYXW68MPFgZt/XP49HqSW918IEZNiBaOiFohIuDJiAyql3NqOu/cEvDf5y7xp+hPqZsBrbwyEDf8U9PQBTe8nVABAURPmSGpg==');
     jo.put('fingerprint','36:a3:17:e5:79:da:32:35:b5:c9:d4:b5:08:cc:88:1f');
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
                DBMS_CLOUD.GET_OBJECT('OCI_CRED_BUCKET', 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/vXQY3Pa31h3Uys7-2hqLa1y_D4gX9mE4FpGWdawAtatjQmFaZUCs6Djh83gQquyW/n/intoraclerohit/b/GenAI-Agents/o/faq.txt')
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