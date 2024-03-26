## Database replication service

This script is meant to be deployed as a cloud function and will allow automatic database dumps to a cloud storage bucket defined by a cron schedule 

### Development steps
Based off of the GCloud guide [here](https://cloud.google.com/sql/docs/mysql/backup-recovery/scheduling-backups#setting-up)
1. Create a bucket `BUCKET` for database dumps
2. Create the following storage role for SQL backups
   ```bash
     gcloud iam roles create ${SQL_ROLE} --project ${PROJECT_ID} \
     --title "SQL Backup role" \
     --description "Grant permissions to backup data from a Cloud SQL instance" \
     --permissions "cloudsql.backupRuns.create"
    ```
3. Grant the service account for your cloud sql instance object user permissions (terminal or console IAM)
    ```bash
    export SQL_SA=(`gcloud sql instances describe ${SQL_INSTANCE} \
    --project ${PROJECT_ID} \
    --format "value(serviceAccountEmailAddress)"`)

    gsutil iam ch serviceAccount:${SQL_SA}:projects/${PROJECT_ID}/roles/storage.objectUser gs://${BUCKET_NAME}
    ```
4. Create a service account for the cloud function 
    ```bash
    gcloud iam service-accounts create ${GCF_NAME} \
    --display-name "Service Account for GCF and SQL Admin API"
   ```
5. Grant the cloud function permission with the custom role in step 2 (terminal or console IAM)
    ```bash
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${GCF_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="projects/${PROJECT_ID}/roles/${SQL_ROLE}"
   ```
6. Also add the following iam policy roles to the above Service Account:
   - Cloud Pub/Sub Service Agent
   - Cloud Run Invoker
   - Cloud SQL Viewer
   - Service Account Token Creator
7. Create a pub/sub topic
    ```bash
    gcloud pubsub topics create ${PUBSUB_TOPIC}
    ```

8. Deploy code in the root folder with the following
    ```bash 
    gcloud functions deploy ${NAME} --trigger-topic ${PUBSUB_TOPIC} --runtime python39 --entry-point main --service-account ${GCF_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --region us-west1
   ```
   - Ensure the function is gen2
9. Create a Cloud Scheduler job
   - First create an App engine instance for the scheduler job
       ```bash
        gcloud app create --region=us-west1
       ```
   - Then create the scheduler job and define parameters of the backup
     ```bash
     gcloud scheduler jobs create pubsub ${SCHEDULER_JOB} \
     --schedule "0 * * * *" \
     --topic ${PUBSUB_TOPIC} \
     --message-body '{"instance":'\"${SQL_INSTANCE}\"',"project":'\"${PROJECT_ID}\"'}' \
     --time-zone 'America/Los_Angeles'```
10. Run the scheduler with `gcloud scheduler jobs run ${SCHEDULER_JOB}`


This code is currently being used by the ss-cord project