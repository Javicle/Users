from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from tools_openverse.common.heath import ServiceCheck, ServiceStatusResponse


class DatabaseHealthService(ServiceCheck):
    def __init__(self, service_name: str, session: AsyncSession):
        super().__init__(service_name=service_name)
        self.service_name = service_name
        self.session = session

    async def check(self) -> ServiceStatusResponse:
        try:
            result = await self.session.execute(text("SELECT 1"))
            if result:
                return ServiceStatusResponse(
                    service_name=self.service_name, success=True, message="Database is healthy"
                )
            return ServiceStatusResponse(
                service_name=self.service_name, success=False, message="Database is unhealthy"
            )
        except Exception as e:
            return ServiceStatusResponse(
                service_name=self.service_name,
                success=False,
                message=f"Database is unhealthy: {str(e)}",
            )


class RedisHealthCheck(ServiceCheck):
    def __init__(self, service_name: str, redis_client: Redis):
        super().__init__(service_name=service_name)
        self.service_name = service_name
        self.redis_client = redis_client

    async def check(self) -> ServiceStatusResponse:
        try:
            await self.redis_client.ping()  # type: ignore[PylancereportUnknownMemberType]
            return ServiceStatusResponse(
                service_name=self.service_name, success=True, message="Redis is healthy"
            )
        except Exception as exc:
            return ServiceStatusResponse(
                service_name=self.service_name,
                success=False,
                message=f"Redis is unhealthy: {str(exc)}",
            )
