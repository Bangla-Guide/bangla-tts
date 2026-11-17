from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # আপনার বর্তমান fetch() ফাংশনের লজিক এখানে বসান
        return Response("OK")
