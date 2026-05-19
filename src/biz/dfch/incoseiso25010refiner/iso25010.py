# Copyright (C) 2026 Ronald Rink, d-fens GmbH, http://d-fens.ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# flake8: noqa=E501
# pylint: disable=C0103
# pylint: disable=C0301

"""ISO25010 characteristics."""

from enum import StrEnum
from dataclasses import dataclass


class Iso25010(StrEnum):
    """ISO25010 main characteristics."""

    FUNCTIONALITY = "Functional Suitability"
    PERFORMANCE = "Performance Efficiency"
    COMPATIBILITY = "Compatibility"
    INTERACTION = "Interaction Capability"
    RELIABILITY = "Reliability"
    SECURITY = "Security"
    MAINTAINABILITY = "Maintainability"
    FLEXIBILITY = "Flexibility"
    SAFETY = "Safety"


class Iso25010Functionality(StrEnum):
    """ISO25010 characteristics and description of 'functional suitability'."""

    FUNCTIONAL_COMPLETENESS = "capability of a product to provide a set of functions that covers all the specified tasks and intended users’ objectives"
    FUNCTIONAL_CORRECTNESS = "capability of a product to provide accurate results when used by intended users"
    FUNCTIONAL_APPROPRIATENESS = "capability of a product to provide functions that facilitate the accomplishment of specified tasks and objectives"


class Iso25010Performance(StrEnum):
    """ISO25010 characteristics and description of 'performance efficiency'."""

    TIME_BEHAVIOUR = "capability of a product to perform its specified function under specified conditions so that the response time and throughput rates meet the requirements"
    RESOURCE_UTILIZATION = "capability of a product to use no more than the specified amount of resources to perform its function under specified conditions"
    CAPACITY = "capability of a product to meet requirements for the maximum limits of a product parameter"


class Iso25010Compatibility(StrEnum):
    """ISO25010 characteristics and description of 'compatibility'."""

    CO_EXISTENCE = "capability of a product to perform its required functions efficiently while sharing a common environment and resources with other products, without detrimental impact on any other product"
    INTEROPERABILITY = "capability of a product to exchange information with other products and mutually use the information that has been exchanged"


class Iso25010InteractionCapability(StrEnum):
    """ISO25010 characteristics and description of 'interaction capability'."""

    APPROPRIATENESS_RECOGNIZABILITY = "capability of a product to be recognized by users as appropriate for their needs"
    LEARNABILITY = "capability of a product to have specified users learn to use specified product functions within a specified amount of time"
    OPERABILITY = "capability of a product to have functions and attributes that make it easy to operate and control"
    USER_ERROR_PROTECTION = "capability of a product to prevent operation errors"
    USER_ENGAGEMENT = "capability of a product to present functions and information in an inviting and motivating manner encouraging continued interaction"
    INCLUSIVITY = "capability of a product to be utilised by people of various backgrounds"
    USER_ASSISTANCE = "capability of a product to be used by people with the widest range of characteristics and capabilities to achieve specified goals in a specified context of use"
    SELF_DESCRIPTIVENESS = "capability of a product to present appropriate information, where needed by the user, to make its capabilities and use immediately obvious to the user without excessive interactions with a product or other resources"


class Iso25010Reliability(StrEnum):
    """ISO25010 characteristics and description of 'reliability'."""

    FAULTLESSNESS = "capability of a product to perform specified functions without fault under normal operation"
    AVAILABILITY = "capability of a product to be operational and accessible when required for use"
    FAULT_TOLERANCE = "capability of a product to operate as intended despite the presence of hardware or software faults"
    RECOVERABILITY = "capability of a product in the event of an interruption or a failure to recover the data directly affected and re-establish the desired state of the system"


class Iso25010Security(StrEnum):
    """ISO25010 characteristics and description of 'security'."""

    CONFIDENTIALITY = "capability of a product to ensure that data are accessible only to those authorized to have access"
    INTEGRITY = "capability of a product to ensure that the state of its system and data are protected from unauthorized modification or deletion either by malicious action or computer error"
    NON_REPUDIATION = "capability of a product to prove that actions or events have taken place, so that the events or actions cannot be repudiated later"
    ACCOUNTABILITY = "capability of a product to enable actions of an entity to be traced uniquely to the entity"
    AUTHENTICITY = "capability of a product to prove that the identity of a subject or resource is the one claimed"
    RESISTANCE = "capability of a product to sustain operations while under attack from a malicious actor"


class Iso25010Maintainability(StrEnum):
    """ISO25010 characteristics and description of 'maintainability'."""

    MODULARITY = "capability of a product to limit changes to one component from affecting other components"
    REUSABILITY = "capability of a product to be used as assets in more than one system, or in building other assets"
    ANALYSABILITY = "capability of a product to be effectively and efficiently assessed regarding the impact of an intended change to one or more of its parts, to diagnose it for deficiencies or causes of failures, or to identify parts to be modified"
    MODIFIABILITY = "capability of a product to be effectively and efficiently modified without introducing defects or degrading existing product quality"
    TESTABILITY = "capability of a product to enable an objective and feasible test to be designed and performed to determine whether a requirement is met"


class Iso25010Flexibility(StrEnum):
    """ISO25010 characteristics and description of 'flexibility'."""

    ADAPTABILITY = "capability of a product to be effectively and efficiently adapted for or transferred to different hardware, software or other operational or usage environments"
    SCALABILITY = "capability of a product to handle growing or shrinking workloads or to adapt its capacity to handle variability"
    INSTALLABILITY = "capability of a product to be effectively and efficiently installed successfully and/or uninstalled in a specified environment"
    REPLACEABILITY = "capability of a product to replace another specified product for the same purpose in the same environment"


class Iso25010Safety(StrEnum):
    """ISO25010 characteristics and description of 'safety'."""

    OPERATIONAL_CONSTRAINT = "capability of a product to constrain its operation to within safe parameters or states when encountering operational hazard"
    RISK_IDENTIFICATION = "capability of a product to identify a course of events or operations that can expose life, property or environment to unacceptable risk"
    FAIL_SAFE = "capability of a product to automatically place itself in a safe operating mode, or to revert to a safe condition in the event of a failure"
    HAZARD_WARNING = "capability of a product to provide warnings of unacceptable risks to operations or internal controls so that they can react in sufficient time to sustain safe operations"
    SAFE_INTEGRATION = "capability of a product to maintain safety during and after integration with one or more components"


@dataclass(frozen=True)
class Iso25010Characteristics:
    """ISO25010 characteristics."""

    FUNCTIONALITY = Iso25010Functionality
    PERFORMANCE = Iso25010Performance
    COMPATIBILITY = Iso25010Compatibility
    INTERACTION = Iso25010InteractionCapability
    RELIABILITY = Iso25010Reliability
    SECURITY = Iso25010Security
    MAINTAINABILITY = Iso25010Maintainability
    FLEXIBILITY = Iso25010Flexibility
    SAFETY = Iso25010Safety
