from src.app.services.print_service import PrintService
from src.core.printer.factory import PrintStrategyFactory
from src.core.printer.manager import PrintManager
from src.core.printer.queue_monitor import PrintQueueMonitor


class AppContainer:
    """
    Centralized Inversion of Control container

    Responsible for wiring up the application's dependency graph.
    It instantiates infrastructure components and injects them into application services.
    """

    def __init__(self, queue_timeout_seconds: int = 45):
        """
        Initializes the application container and resolves dependencies

        Args:
            queue_timeout_seconds (int, optional): Maximum time in seconds to wait for
            the hardware print queue to clear. Defaults to 45.
        """

        # Low-level infrastructure
        self.monitor = PrintQueueMonitor(timeout_seconds=queue_timeout_seconds)

        # Mid-level infrastructure and factories
        self.print_manager = PrintManager(queue_monitor=self.monitor)
        self.strategy_factory = PrintStrategyFactory()

        # Inject infrastructure into high-level application service

        self.print_service = PrintService(
            print_manager=self.print_manager, strategy_factory=self.strategy_factory
        )
