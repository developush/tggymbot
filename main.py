from telegram import Update
from telegram.ext import (
    filters,
    Application,
    PicklePersistence,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler
)

from config import TOKEN
from logic.base import Registration
from logic.training import (
    MuscleGroupsController,
    ExerciseToolController,
    GroupExercisesController,
    ExerciseController,
    StartExerciseController,
    UpdateSetController,
    CheckEndTrainingController,
    EndTrainingController
)
from logic.analytics import (
    AnalyticsMenuController,
    AnalyticsGeneratorController,
    MyTrainingsController
)
from logic.settings import (
    SettingsController,
    NotificationsController,
    LanguageController,
    LanguageSetterController
)
from logic.subscription import (
    SubscriptionMenuController,
    InvoiceController,
    CheckoutController,
    SuccessInvoiceController,
)
from logic.info import (
    InfoMenuController,
    InfoManualController,
    FeedbackController,
    OfertaController,
    HelpController,
    GuideController
)
from logic.calculator import (
    CalculatorGenderController,
    CalculatorLevelController,
    CalculatorParamsController,
    CalculatorResultController
)

from logic.programs import (
    ProgramGroupController,
    ProgramLevelController,
    ProgramController,
    StopProgramController,
    NextDayProgramController
)


def init_app():
    persistence = PicklePersistence(filepath="gymbuddybot")

    application = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )
    add_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def add_handlers(application):
    # start handler
    application.add_handler(CommandHandler("start",
                                           Registration(application).set_start().call))

    # callbacks handlers
    application.add_handler(CallbackQueryHandler(MuscleGroupsController(application).call,
                                                 pattern=MuscleGroupsController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(ExerciseToolController(application).call,
                                                 pattern=ExerciseToolController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(GroupExercisesController(application).call,
                                                 pattern=GroupExercisesController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(ExerciseController(application).call,
                                                 pattern=ExerciseController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(StartExerciseController(application).call,
                                                 pattern=StartExerciseController.pattern,
                                                 block=False))
    application.add_handler(MessageHandler((filters.UpdateType.EDITED_MESSAGE &
                                            (filters.Regex(UpdateSetController.pattern())) |
                                            filters.Regex(UpdateSetController.extended_pattern())),
                                           UpdateSetController(application).call,
                                           block=False))
    application.add_handler(MessageHandler((filters.Regex(UpdateSetController.pattern()) |
                                            filters.Regex(UpdateSetController.extended_pattern())),
                                           UpdateSetController(application).call,
                                           block=False))
    application.add_handler(CallbackQueryHandler(MyTrainingsController(application).call,
                                                 pattern=MyTrainingsController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(CheckEndTrainingController(application).call,
                                                 pattern=CheckEndTrainingController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(EndTrainingController(application).call,
                                                 pattern=EndTrainingController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(AnalyticsMenuController(application).call,
                                                 pattern=AnalyticsMenuController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(AnalyticsGeneratorController(application).call,
                                                 pattern=AnalyticsGeneratorController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(AnalyticsGeneratorController(application).call,
                                                 pattern=AnalyticsGeneratorController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(SettingsController(application).call,
                                                 pattern=SettingsController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(NotificationsController(application).call,
                                                 pattern=NotificationsController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(LanguageController(application).call,
                                                 pattern=LanguageController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(LanguageSetterController(application).call,
                                                 pattern=LanguageSetterController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(SubscriptionMenuController(application).call,
                                                 pattern=SubscriptionMenuController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(InvoiceController(application).call,
                                                 pattern=InvoiceController.pattern,
                                                 block=False))
    application.add_handler(PreCheckoutQueryHandler(CheckoutController(application).call,
                                                    block=True))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT,
                                           SuccessInvoiceController(application).call,
                                           block=True))
    application.add_handler(CallbackQueryHandler(InfoMenuController(application).call,
                                                 pattern=InfoMenuController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(InfoManualController(application).call,
                                                 pattern=InfoManualController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(FeedbackController(application).call,
                                                 pattern=FeedbackController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(OfertaController(application).call,
                                                 pattern=OfertaController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(HelpController(application).call,
                                                 pattern=HelpController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(GuideController(application).call,
                                                 pattern=GuideController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(CalculatorGenderController(application).call,
                                                 pattern=CalculatorGenderController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(CalculatorLevelController(application).call,
                                                 pattern=CalculatorLevelController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(CalculatorParamsController(application).call,
                                                 pattern=CalculatorParamsController.pattern,
                                                 block=False))
    application.add_handler(MessageHandler(filters.Regex(CalculatorResultController.pattern()),
                                           CalculatorResultController(application).call,
                                           block=False))
    application.add_handler(CallbackQueryHandler(ProgramGroupController(application).call,
                                                 pattern=ProgramGroupController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(ProgramLevelController(application).call,
                                                 pattern=ProgramLevelController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(ProgramController(application).call,
                                                 pattern=ProgramController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(StopProgramController(application).call,
                                                 pattern=StopProgramController.pattern,
                                                 block=False))
    application.add_handler(CallbackQueryHandler(NextDayProgramController(application).call,
                                                 pattern=NextDayProgramController.pattern,
                                                 block=False))

    application.add_handler(CallbackQueryHandler(Registration(application).set_bot_menu().call,
                                                 pattern='menu',
                                                 block=False))

    # commands handlers
    application.add_handler(CommandHandler('start', Registration(application).set_start().call, block=False))
    application.add_handler(CommandHandler('menu', Registration(application).set_bot_menu().call, block=False))
    application.add_handler(CommandHandler('end_training', EndTrainingController(application).call, block=False))
    application.add_handler(CommandHandler('info', InfoMenuController(application).call, block=False))
    application.add_handler(CommandHandler('information', InfoMenuController(application).call, block=False))
    application.add_handler(CommandHandler('help', HelpController(application).call, block=False))
    application.add_handler(CommandHandler('show_analytics', AnalyticsMenuController(application).call, block=False))
    application.add_handler(CommandHandler('subscription', SubscriptionMenuController(application).call, block=False))
    application.add_handler(CommandHandler('settings', SettingsController(application).call, block=False))


if __name__ == '__main__':
    init_app()
