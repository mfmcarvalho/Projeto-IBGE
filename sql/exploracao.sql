SELECT current_database(), current_user;

#FatoPIB
#PK codigo_ibge, ano, pib_total
select * from ibge.fact_pib limit 10;

#PK codigo_ibge, nome_municipio, codigo_uf
select * from ibge.dim_cidade limit 10;

#PK codigo_uf, nome_uf, sigla_uf, codigo_regiao
select * from ibge.dim_uf

#PK codigo_regiao, nome_regiao
select * from ibge.dim_regiao limit 10;

SELECT
    current_database(),
    current_user;



#Inspecionando o banco:
SELECT
    table_schema AS schema,
    table_name AS tabela,
    ordinal_position AS posicao,
    column_name AS coluna,
    data_type AS tipo,
    is_nullable AS aceita_null
FROM information_schema.columns
WHERE table_schema = 'ibge'
ORDER BY
    table_name,
    ordinal_position;



#Determinando PIB  total
#e share do PIB por município
WITH pib_cidade AS (
    SELECT 
        dc.nome_municipio,
        SUM(fb.pib_total) AS pib_total
    FROM ibge.dim_cidade dc
    INNER JOIN ibge.fact_pib fb
        ON dc.codigo_ibge = fb.codigo_ibge
    GROUP BY dc.nome_municipio
)
SELECT 
    nome_municipio,
    pib_total,

    ROUND(
        (
            100 * pib_total /
            SUM(pib_total) OVER ()
        )::NUMERIC,
        2
    ) AS share_pib
FROM pib_cidade
ORDER BY share_pib DESC;


#Determinando PIB total por região:
#PK codigo_ibge, ano, pib_total
select * from ibge.fact_pib limit 10;

#PK codigo_ibge, nome_municipio, codigo_uf
select * from ibge.dim_cidade limit 10;

#PK codigo_uf, nome_uf, sigla_uf, codigo_regiao
select * from ibge.dim_uf

USE ibge;
select ibge.dim_regiao.codigo_regiao, ibge.dim_regiao.nome_regiao, SUM(ibge.fact_pib.pib_total) AS pib_total
from ibge.dim_regiao
inner join ibge.dim_uf 
    on ibge.dim_regiao.codigo_regiao = ibge.dim_uf.codigo_regiao
INNER JOIN ibge.dim_cidade
    on ibge.dim_uf.codigo_uf = ibge.dim_cidade.codigo_uf
INNER JOIN ibge.fact_pib
    on ibge.dim_cidade.codigo_ibge = ibge.fact_pib.codigo_ibge
GROUP BY ibge.dim_regiao.codigo_regiao, ibge.dim_regiao.nome_regiao

select * from fact_pib limit 10;

#Municipios com maior share de pib de agropecuária
select dc.nome_municipio, 
sum(fb.vab_agropecuaria)/sum(fb.pib_total)*100 as share_agropecuaria
from 
ibge.dim_cidade dc inner join
ibge.fact_pib fb on dc.codigo_ibge = fb.codigo_ibge
group by dc.nome_municipio
order by share_agropecuaria asc
limit 10;


