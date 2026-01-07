import styles from './workflowCard.module.css';
import { WorkflowCardVO } from './WorkflowCardVO';
import { useTranslation } from 'react-i18next';

export default function WorkflowCard({ cardVO }: { cardVO: WorkflowCardVO }) {
  const { t } = useTranslation();

  return (
    <div className={`${styles.cardContainer}`}>
      <div className={`${styles.basicInfoContainer}`}>
        <div className={`${styles.basicInfoNameContainer}`}>
          <div className={`${styles.basicInfoNameText} ${styles.bigText}`}>
            {cardVO.name}
          </div>
          <div className={`${styles.basicInfoDescriptionText}`}>
            {cardVO.description || t('pipelines.noDescription')}
          </div>
        </div>

        <div className={`${styles.basicInfoLastUpdatedTimeContainer}`}>
          <svg
            className={`${styles.basicInfoUpdateTimeIcon}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20ZM13 12H17V14H11V7H13V12Z"></path>
          </svg>
          <div className={`${styles.basicInfoUpdateTimeText}`}>
            {t('pipelines.updateTime')}
            {cardVO.lastUpdatedTimeAgo}
          </div>
        </div>
      </div>

      <div className={styles.operationContainer}>
        {cardVO.status === 'active' && (
          <div className={styles.operationDefaultBadge}>
            <svg
              className={styles.operationDefaultBadgeIcon}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M17 3H7C5.9 3 5 3.9 5 5V21L12 18L19 21V5C19 3.9 18.1 3 17 3ZM17 18L12 15.82L7 18V5H17V18Z"></path>
            </svg>
            <div className={styles.operationDefaultBadgeText}>
              {t('workflow.active')}
            </div>
          </div>
        )}
        <div className={styles.workflowBadge}>
          <svg
            className={styles.workflowBadgeIcon}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M7 3C5.9 3 5 3.9 5 5C5 6.1 5.9 7 7 7C8.1 7 9 6.1 9 5C9 3.9 8.1 3 7 3ZM7 11C5.9 11 5 11.9 5 13C5 14.1 5.9 15 7 15C8.1 15 9 14.1 9 13C9 11.9 8.1 11 7 11ZM7 19C5.9 19 5 19.9 5 21C5 22.1 5.9 23 7 23C8.1 23 9 22.1 9 21C9 19.9 8.1 19 7 19ZM17 3C15.9 3 15 3.9 15 5C15 6.1 15.9 7 17 7C18.1 7 19 6.1 19 5C19 3.9 18.1 3 17 3ZM17 7C16.72 7 16.47 6.89 16.29 6.71L13 10L16.29 13.29C16.47 13.11 16.72 13 17 13C18.1 13 19 13.9 19 15C19 16.1 18.1 17 17 17C15.9 17 15 16.1 15 15C15 14.72 15.11 14.47 15.29 14.29L12 11L8.71 14.29C8.89 14.47 9 14.72 9 15C9 16.1 8.1 17 7 17C5.9 17 5 16.1 5 15C5 13.9 5.9 13 7 13C7.28 13 7.53 13.11 7.71 13.29L11 10L7.71 6.71C7.53 6.89 7.28 7 7 7"></path>
          </svg>
          <div className={styles.workflowBadgeText}>
            {t('workflow.workflowBadge')}
          </div>
        </div>
      </div>
    </div>
  );
}