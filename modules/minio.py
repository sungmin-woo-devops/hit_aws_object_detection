import boto3
import botocore
from botocore.exceptions import ClientError
from typing import Any, List, Optional

s3 = boto3.client(
    's3',
    endpoint_url='http://100.97.183.123:9000',
    aws_access_key_id='minio',
    aws_secret_access_key='miniosecret'
)

# 연결 확인
def check_bucket_connection(bucket_name: str) -> bool:
    try:
        s3.list_buckets()['Buckets']
        return True
    except ClientError as e:
        print(e)
        return False

# 버킷 리스트 조회
def list_buckets() -> list:
    try:
        response = s3.list_buckets()
        return response['Buckets']
    except Exception as e:
        print(f"버킷 리스트 조회 실패: {e}")
        return []

# 버킷 생성
def create_bucket(bucket_name: str) -> bool:
    try:
        s3.create_bucket(
            Bucket=bucket_name, 
            CreateBucketConfiguration={
                'LocationConstraint': 'ap-northeast-2'
            }
        )
        print(f"버킷 {bucket_name} 생성 완료")
        return True
    except Exception as e:
        print(f"버킷 {bucket_name} 생성 실패: {e}")
        return False

def list_files_in_directory(bucket_name: str, directory: str) -> List[dict[str, Any]]:
    """
    특정 버킷 내 디렉토리(접두사) 하위 파일을 조회합니다.
    
    Args:
        bucket_name: 버킷 이름
        directory: 디렉토리 이름 (예: 'preprocessed/')
    
    Returns:
        파일 정보 리스트
    """
    if not directory.endswith('/'):
        directory += '/'

    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=directory)
        return response.get('Contents', [])
    except Exception as e:
        print(f"{bucket_name}/{directory} 내 파일 조회 실패: {e}")
        return []

def list_directories(bucket_name: str, prefix: str = "") -> List[str]:
    """
    버킷 내 상위 디렉토리(폴더) 목록을 조회합니다.
    
    Args:
        bucket_name: 버킷 이름
        prefix: 접두사 필터 (예: 'data/') — 없으면 루트 기준
    
    Returns:
        디렉토리 이름 리스트
    """
    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            Delimiter='/'
        )
        return [cp['Prefix'] for cp in response.get('CommonPrefixes', [])]
    except Exception as e:
        print(f"{bucket_name}/{prefix} 폴더 리스트 조회 실패: {e}")
        return []


def list_files(bucket_name: str) -> List[dict[str, Any]]:
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        return response.get('Contents', [])
    except Exception as e:
        print(f"파일 조회 실패: {e}")
        return []

def head_files(bucket_name: str, n: int = 100) -> List[dict[str, Any]]:
    """
    버킷에서 최신 파일 n개를 조회합니다.
    
    Args:
        bucket_name: 조회할 버킷 이름
        n: 조회할 파일 개수 (기본값: 100)
    
    Returns:
        파일 정보 리스트 (LastModified 기준 내림차순 정렬)
    """
    try:
        files = list_files(bucket_name)
        if not files:
            return []
        
        # LastModified 기준으로 내림차순 정렬 (최신 파일이 먼저)
        sorted_files = sorted(files, key=lambda x: x.get('LastModified', ''), reverse=True)
        
        return sorted_files[:n]
    except Exception as e:
        print(f"파일 조회 실패: {e}")
        return []

# 버킷 내 디렉터리 생성
def create_directory(bucket_name: str, directory_name: str) -> bool:
    try:
        if not directory_name.endswith('/'):
            directory_name += '/'
        s3.put_object(Bucket=bucket_name, Key=directory_name)
        print(f"디렉터리 {directory_name} 생성 완료")
        return True
    except Exception as e:
        print(f"디렉터리 {directory_name} 생성 실패: {e}")
        return False

# 파일 업로드
def upload_file(bucket_name: str, file_path: str, key: str, quiet: bool = False) -> bool:
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
        if not quiet:
            print(f"파일 {key} 이미 존재합니다.")
        return False
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                s3.upload_file(file_path, bucket_name, key)
                if not quiet:
                    print(f"파일 {key} 업로드 완료")
                return True
            except Exception as e:
                if not quiet:
                    print(f"파일 {key} 업로드 실패: {e}")
                return False
        else:
            if not quiet:
                print(f"S3 접근 오류: {e}")
            return False

# 파일 다운로드
def download_file(bucket_name: str, key: str, local_path: str, quiet: bool = True) -> bool:
    try:
        s3.download_file(bucket_name, key, local_path)
        if not quiet:
            print(f"파일 {key} 다운로드 완료")
        return True
    except Exception as e:
        if not quiet:
            print(f"파일 {key} 다운로드 실패: {e}")
        return False

def get_file_info(bucket_name: str, key: str) -> Optional[dict[str, Any]]:
    """
    특정 파일의 상세 정보를 조회합니다.
    
    Args:
        bucket_name: 버킷 이름
        key: 파일 키
    
    Returns:
        파일 정보 딕셔너리 또는 None
    """
    try:
        response = s3.head_object(Bucket=bucket_name, Key=key)
        return {
            'Key': key,
            'Size': response.get('ContentLength'),
            'LastModified': response.get('LastModified'),
            'ETag': response.get('ETag'),
            'ContentType': response.get('ContentType'),
            'Metadata': response.get('Metadata', {})
        }
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"파일 {key}를 찾을 수 없습니다.")
        else:
            print(f"파일 정보 조회 실패: {e}")
        return None

def list_files_by_prefix(bucket_name: str, prefix: str = "") -> List[dict[str, Any]]:
    """
    특정 접두사로 시작하는 파일들을 조회합니다.
    
    Args:
        bucket_name: 버킷 이름
        prefix: 파일 키 접두사
    
    Returns:
        파일 정보 리스트
    """
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return response.get('Contents', [])
    except Exception as e:
        print(f"접두사 파일 조회 실패: {e}")
        return []

def delete_file(bucket_name: str, key: str) -> bool:
    """
    파일을 삭제합니다.
    
    Args:
        bucket_name: 버킷 이름
        key: 파일 키
    
    Returns:
        삭제 성공 여부
    """
    try:
        s3.delete_object(Bucket=bucket_name, Key=key)
        print(f"파일 {key} 삭제 완료")
        return True
    except Exception as e:
        print(f"파일 {key} 삭제 실패: {e}")
        return False

# 사용 예시:
# s3.create_bucket(Bucket='hit-dl')
# s3.upload_file('local_file.txt', 'hit-dl', 'remote_file.txt')
# s3.download_file('my-bucket', 'remote_file.txt', 'downloaded.txt')
# s3.delete_object(Bucket='my-bucket', Key='remote_file.txt')
# response = s3.list_objects_v2(Bucket='hit-dl')
# for obj in response('Contents', []):
#     print(obj['Key'])

