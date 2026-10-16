FROM apache/spark:4.1.3-java21-python3

USER root
WORKDIR /opt/spark/jars
ARG MAVEN=https://repo1.maven.org/maven2

# Kafka connector
RUN curl -fsSLO $MAVEN/org/apache/spark/spark-sql-kafka-0-10_2.13/4.1.3/spark-sql-kafka-0-10_2.13-4.1.3.jar \
 && curl -fsSLO $MAVEN/org/apache/spark/spark-token-provider-kafka-0-10_2.13/4.1.3/spark-token-provider-kafka-0-10_2.13-4.1.3.jar \
 && curl -fsSLO $MAVEN/org/apache/kafka/kafka-clients/3.9.1/kafka-clients-3.9.1.jar \
 && curl -fsSLO $MAVEN/org/apache/commons/commons-pool2/2.12.1/commons-pool2-2.12.1.jar
# Delta Lake (built for Spark 4.1)
RUN curl -fsSLO $MAVEN/io/delta/delta-spark_4.1_2.13/4.4.1/delta-spark_4.1_2.13-4.4.1.jar \
 && curl -fsSLO $MAVEN/io/delta/delta-storage/4.4.1/delta-storage-4.4.1.jar
# S3 access
RUN curl -fsSLO $MAVEN/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar \
 && curl -fsSLO $MAVEN/software/amazon/s3/analyticsaccelerator/analyticsaccelerator-s3/1.2.1/analyticsaccelerator-s3-1.2.1.jar
# AWS SDK: 640 MB, so it gets its own layer and is cached after the first build
RUN curl -fsSLO $MAVEN/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar

WORKDIR /opt/spark/work-dir
USER spark
