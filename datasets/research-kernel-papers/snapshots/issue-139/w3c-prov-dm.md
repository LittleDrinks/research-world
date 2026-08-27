# PROV-DM: The PROV Data Model

## W3C Recommendation 30 April 2013

This version:

http://www.w3.org/TR/2013/REC-prov-dm-20130430/

Latest published version:

http://www.w3.org/TR/prov-dm/

Implementation report:

http://www.w3.org/TR/2013/NOTE-prov-implementations-20130430/

Previous version:

http://www.w3.org/TR/2013/PR-prov-dm-20130312/ (color-coded diff)

Editors:

Luc Moreau , University of Southampton

Paolo Missier , Newcastle University

Contributors:

Khalid Belhajjame , University of Manchester

Reza B'Far , Oracle Corporation

James Cheney , University of Edinburgh

Sam Coppens , iMinds - Ghent University

Stephen Cresswell , legislation.gov.uk

Yolanda Gil , Invited Expert

Paul Groth , VU University of Amsterdam

Graham Klyne , University of Oxford

Timothy Lebo , Rensselaer Polytechnic Institute

Jamie McCusker , Rensselaer Polytechnic Institute

Simon Miles , Invited Expert

James Myers , Rensselaer Polytechnic Institute

Satya Sahoo , Case Western Reserve University

Curt Tilmes , National Aeronautics and Space Administration

Please refer to the errata for this document, which may include some normative corrections.

The English version of this specification is the only normative version. Non-normative translations may also be available.

Copyright © 2011-2013 W3C ® ( MIT , ERCIM , Keio , Beihang ), All Rights Reserved. W3C liability , trademark and document use rules apply.

## Abstract

Provenance is information about entities, activities, and people involved in producing a piece of data or thing, which can be used to form assessments about its quality, reliability or trustworthiness. PROV-DM is the conceptual data model that forms a basis for the W3C provenance (PROV) family of specifications. PROV-DM distinguishes core structures, forming the essence of provenance information, from extended structures catering for more specific uses of provenance. PROV-DM is organized in six components, respectively dealing with: (1) entities and activities, and the time at which they were created, used, or ended; (2) derivations of entities from entities; (3) agents bearing responsibility for entities that were generated and activities that happened; (4) a notion of bundle, a mechanism to support provenance of provenance; (5) properties to link entities that refer to the same thing; and, (6) collections forming a logical structure for its members.

This document introduces the provenance concepts found in PROV and defines PROV-DM types and relations. The PROV data model is domain-agnostic, but is equipped with extensibility points allowing domain-specific information to be included.

Two further documents complete the specification of PROV-DM. First, a companion document specifies the set of constraints that provenance should follow. Second, a separate document describes a provenance notation for expressing instances of provenance for human consumption; this notation is used in examples in this document.

The PROV Document Overview describes the overall state of PROV, and should be read before other PROV documents.

## Status of This Document

This section describes the status of this document at the time of its publication. Other documents may supersede this document. A list of current W3C publications and the latest revision of this technical report can be found in the W3C technical reports index at http://www.w3.org/TR/.

#### PROV Family of Documents

This document is part of the PROV family of documents, a set of documents defining various aspects that are necessary to achieve the vision of inter-operable interchange of provenance information in heterogeneous environments such as the Web. These documents are listed below. Please consult the [ PROV-OVERVIEW ] for a guide to reading these documents.

- PROV-OVERVIEW (Note), an overview of the PROV family of documents [ PROV-OVERVIEW ];

- PROV-PRIMER (Note), a primer for the PROV data model [ PROV-PRIMER ];

- PROV-O (Recommendation), the PROV ontology, an OWL2 ontology allowing the mapping of the PROV data model to RDF [ PROV-O ];

- PROV-DM (Recommendation), the PROV data model for provenance (this document);

- PROV-N (Recommendation), a notation for provenance aimed at human consumption [ PROV-N ];

- PROV-CONSTRAINTS (Recommendation), a set of constraints applying to the PROV data model [ PROV-CONSTRAINTS ];

- PROV-XML (Note), an XML schema for the PROV data model [ PROV-XML ];

- PROV-AQ (Note), mechanisms for accessing and querying provenance [ PROV-AQ ];

- PROV-DICTIONARY (Note) introduces a specific type of collection, consisting of key-entity pairs [ PROV-DICTIONARY ];

- PROV-DC (Note) provides a mapping between PROV-O and Dublin Core Terms [ PROV-DC ];

- PROV-SEM (Note), a declarative specification in terms of first-order logic of the PROV data model [ PROV-SEM ];

- PROV-LINKS (Note) introduces a mechanism to link across bundles [ PROV-LINKS ].

#### Endorsed By W3C

This document has been reviewed by W3C Members, by software developers, and by other W3C groups and interested parties, and is endorsed by the Director as a W3C Recommendation. It is a stable document and may be used as reference material or cited from another document. W3C 's role in making the Recommendation is to draw attention to the specification and to promote its widespread deployment. This enhances the functionality and interoperability of the Web.

#### Please Send Comments

This document was published by the Provenance Working Group as a Recommendation. If you wish to make comments regarding this document, please send them to public-prov-comments@w3.org ( subscribe , archives ). All comments are welcome.

This document was produced by a group operating under the 5 February 2004 W3C Patent Policy . W3C maintains a public list of any patent disclosures made in connection with the deliverables of the group; that page also includes instructions for disclosing a patent. An individual who has actual knowledge of a patent which the individual believes contains Essential Claim(s) must disclose the information in accordance with section 6 of the W3C Patent Policy .

## Table of Contents

- 1. Introduction

- 1.1 Compliance with this Document

- 1.2 Structure of this Document

- 1.3 Notational Conventions

- 1.4 Namespaces

- 2. PROV Overview

- 2.1 PROV Core Structures

- 2.1.1 Entity and Activity

- 2.1.2 Derivation

- 2.1.3 Agents and Responsibility

- 2.2 PROV Extended Structures

- 2.2.1 Mechanisms to Define Extended Structures

- 2.2.1.1 Subtyping

- 2.2.1.2 Expanded Relations

- 2.2.1.3 Optional Identification

- 2.2.1.4 Further Relations

- 2.2.2 Provenance of Provenance

- 2.2.3 Collections

- 2.3 Modular Organization

- 3. The Provenance Notation

- 4. Illustration of PROV-DM by an Example

- 4.1 Example: The Authors View

- 4.2 Example: The Process View

- 4.3 Example: Attribution of Provenance

- 5. PROV-DM Types and Relations

- 5.1 Component 1: Entities and Activities

- 5.1.1 Entity

- 5.1.2 Activity

- 5.1.3 Generation

- 5.1.4 Usage

- 5.1.5 Communication

- 5.1.6 Start

- 5.1.7 End

- 5.1.8 Invalidation

- 5.2 Component 2: Derivations

- 5.2.1 Derivation

- 5.2.2 Revision

- 5.2.3 Quotation

- 5.2.4 Primary Source

- 5.3 Component 3: Agents, Responsibility, and Influence

- 5.3.1 Agent

- 5.3.2 Attribution

- 5.3.3 Association

- 5.3.4 Delegation

- 5.3.5 Influence

- 5.4 Component 4: Bundles

- 5.4.1 Bundle constructor

- 5.4.2 Bundle Type

- 5.5 Component 5: Alternate Entities

- 5.5.1 Specialization

- 5.5.2 Alternate

- 5.6 Component 6: Collections

- 5.6.1 Collection

- 5.6.2 Membership

- 5.7 Further Elements of PROV-DM

- 5.7.1 Identifier

- 5.7.2 Attribute

- 5.7.2.1 prov:label

- 5.7.2.2 prov:location

- 5.7.2.3 prov:role

- 5.7.2.4 prov:type

- 5.7.2.5 prov:value

- 5.7.3 Value

- 5.7.4 Namespace Declaration

- 5.7.5 Qualified Name

- 6. PROV-DM Extensibility Points

- 7. Creating Valid Provenance

- A. Cross-References to PROV-O and PROV-N

- B. Change Log

- B.1 Changes since Proposed Recommendation

- B.2 Changes since Candidate Recommendation

- B.3 Changes since Last Call

- C. Acknowledgements

- D. References

- D.1 Normative references

- D.2 Informative references

## 1. Introduction

For the purpose of this specification, provenance ◊ is defined as a record that describes the people, institutions, entities, and activities involved in producing, influencing, or delivering a piece of data or a thing. In particular, the provenance of information is crucial in deciding whether information is to be trusted, how it should be integrated with other diverse information sources, and how to give credit to its originators when reusing it. In an open and inclusive environment such as the Web, where users find information that is often contradictory or questionable, provenance can help those users to make trust judgements.

We present the PROV data model, PROV-DM, a generic data model for provenance that allows domain and application specific representations of provenance to be translated into such a data model and interchanged between systems. Thus, heterogeneous systems can export their native provenance into such a core data model, and applications that need to make sense of provenance can then import it, process it, and reason over it.

The PROV data model distinguishes core structures from extended structures : core structures form the essence of provenance information, and are commonly found in various domain-specific vocabularies that deal with provenance or similar kinds of information [ Mappings ]. Extended structures enhance and refine core structures with more expressive capabilities to cater for more advanced uses of provenance. The PROV data model, comprising both core and extended structures, is a domain-agnostic model, but with clear extensibility points allowing further domain-specific and application-specific extensions to be defined.

The PROV data model has a modular design and is structured according to six components covering various facets of provenance:

- component 1: entities and activities, and the time at which they were created, used, or ended;

- component 2: derivations of entities from others;

- component 3: agents bearing responsibility for entities that were generated and activities that happened;

- component 4: bundles, a mechanism to support provenance of provenance;

- component 5: properties to link entities that refer to the same thing;

- component 6: collections forming a logical structure for its members.

This specification presents the concepts of the PROV data model, and provenance types and relations, without specific concern for how they are applied. With these, it becomes possible to write useful provenance, and publish or embed it alongside the data it relates to.

However, if something about which provenance is expressed is subject to change, then it is challenging to express its provenance precisely (e.g. the data from which a daily weather report is derived changes from day to day). This is addressed in a companion specification [ PROV-CONSTRAINTS ] by proposing formal constraints on the way that provenance is related to the things it describes (such as the use of attributes, temporal information and specialization of entities), and additional conclusions that are valid to infer.

### 1.1 Compliance with this Document

For the purpose of compliance, the normative sections of this document are Section 1.1 , Section 1.3 , Section 5. , and Appendix A .

- Information in tables is normative if it appears in a normative section.

- All figures (including UML diagrams) are informative.

- Text in boxes labeled "Example" is informative.

### 1.2 Structure of this Document

This section is non-normative.

Section 2 provides an overview of the PROV data model, distinguishing a core set of types and relations, commonly found in provenance, from extended structures catering for more specific uses. It also introduces a modular organization of the data model in components.

Section 3 overviews the Provenance Notation used to illustrate examples of provenance.

Section 4 illustrates how the PROV data model can be used to express the provenance of a report published on the Web.

Section 5 provides the definitions of PROV concepts, structured according to six components.

Section 6 summarizes PROV-DM extensibility points.

Section 7 introduces the idea that constraints can be applied to the PROV data model to validate provenance; these are covered in the companion specification [ PROV-CONSTRAINTS ].

### 1.3 Notational Conventions

The key words " MUST ", " MUST NOT ", " REQUIRED ", " SHALL ", " SHALL NOT ", " SHOULD ", " SHOULD NOT ", " RECOMMENDED ", " MAY ", and " OPTIONAL " in this document are to be interpreted as described in [ RFC2119 ].

Examples throughout this document use the PROV-N Provenance Notation, briefly introduced in Section 3 and specified fully in a separate document [ PROV-N ].

### 1.4 Namespaces

This section is non-normative.

The following namespaces prefixes are used throughout this document.

Table 1 ◊: Prefix and Namespaces used in this specification prefix

namespace IRI

definition

prov

http://www.w3.org/ns/prov#

The PROV namespace (see Section 5.7.4 )

xsd

http://www.w3.org/2000/10/XMLSchema#

XML Schema Namespace [ XMLSCHEMA11-2 ]

rdf

http://www.w3.org/1999/02/22-rdf-syntax-ns#

The RDF namespace [ RDF-CONCEPTS ]

(others)

(various)

All other namespace prefixes are used in examples only.

In particular, IRIs starting with "http://example.com" represent

some application-dependent IRI [ RFC3987 ]

## 2. PROV Overview

This section is non-normative.

This section introduces provenance concepts with informal explanations and illustrative examples. PROV distinguishes core structures , forming the essence of provenance, from extended structures catering for more specific uses of provenance. Core and extended structures are respectively presented in Section 2.1 and Section 2.2 . Furthermore, the PROV data model is organized according to components, which form thematic groupings of concepts (see Section 2.3 ). A provenance description is an instance of a provenance structure, whether core or extended, described below.

### 2.1 PROV Core Structures

This section is non-normative.

At its core, provenance describes the use and production of entities by activities , which may be influenced in various ways by agents . These core types and their relationships are illustrated by the UML diagram of Figure 1 .

Figure 1 ◊: PROV Core Structures (Informative)

The concepts found in the core of PROV are introduced in the rest of this section. They are summarized in Table 2 , where they are categorized as type or relation. The first column lists concepts, the second column indicates whether a concept maps to a type or a relation, whereas the third column contains the corresponding name, as it appears in Figure 1. Names of relations have a verbal form in the past tense to express what happened in the past, as opposed to what may or will happen. In the core of PROV, all relations are binary.

Table 2 ◊: Mapping of PROV core concepts to types and relations PROV Concepts

PROV-DM types or relations

Name

Overview

Entity

PROV-DM Types

Entity

Section 2.1.1

Activity

Activity

Section 2.1.1

Agent

Agent

Section 2.1.3

Generation

PROV-DM Relations

WasGeneratedBy

Section 2.1.1

Usage

Used

Section 2.1.1

Communication

WasInformedBy

Section 2.1.1

Derivation

WasDerivedFrom

Section 2.1.2

Attribution

WasAttributedTo

Section 2.1.3

Association

WasAssociatedWith

Section 2.1.3

Delegation

ActedOnBehalfOf

Section 2.1.3
